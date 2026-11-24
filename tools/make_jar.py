#!/usr/bin/env python3
"""Build the empty Forge 1.20.1 mod JAR without a JDK or network access.

Why this exists
---------------
This workspace has no Java toolchain and cannot reach maven.minecraftforge.net,
so `gradle build` cannot run here. This script assembles the exact same four-file
JAR directly from the sources that build.gradle would package:

    META-INF/MANIFEST.MF
    META-INF/mods.toml       (placeholders expanded from gradle.properties)
    pack.mcmeta              (placeholders expanded from gradle.properties)
    <package>/SpaceCraft.class  (equivalent to javac -target 17 output)

On a normal machine `gradle build` produces the equivalent artifact.

Usage
-----
    python3 tools/make_jar.py              # build dist/spacecraft-1.0.0.jar
    python3 tools/make_jar.py --check      # only verify an existing JAR
    python3 tools/make_jar.py --out X.jar  # custom output path
"""

from __future__ import annotations

import argparse
import json
import os
import re
import string
import struct
import sys
import tomllib
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Java class file constants
MAGIC = b"\xca\xfe\xba\xbe"
MAJOR_VERSION = 61  # Java 17, required by Minecraft / Forge 1.20.1
ACC_PUBLIC = 0x0001
ACC_SUPER = 0x0020
MOD_ANNOTATION_DESC = "Lnet/minecraftforge/fml/common/Mod;"


# --------------------------------------------------------------------------
# gradle.properties + source discovery
# --------------------------------------------------------------------------
def read_properties(path: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid gradle.properties line: {line!r}")
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def expand(text: str, props: dict[str, str]) -> str:
    """Same ${key} substitution as Gradle's `expand` in processResources."""
    return string.Template(text).substitute(props)


def find_entry_point(props: dict[str, str]) -> tuple[str, str, str]:
    """Return (package path, class name, mod id) read from the real .java file."""
    sources = sorted((ROOT / "src/main/java").rglob("*.java"))
    if len(sources) != 1:
        raise ValueError(f"Expected exactly one @Mod class, found {len(sources)}: {sources}")
    src = sources[0]
    text = src.read_text(encoding="utf-8")

    pkg_match = re.search(r"^package\s+([\w.]+)\s*;", text, re.M)
    mod_match = re.search(r'@Mod\(\s*"([^"]+)"\s*\)', text)
    if not pkg_match or not mod_match:
        raise ValueError("Entry point must declare a package and an @Mod(\"...\") annotation")

    package = pkg_match.group(1)
    mod_id = mod_match.group(1)
    if mod_id != props["mod_id"]:
        raise ValueError(f"@Mod id {mod_id!r} != gradle.properties mod_id {props['mod_id']!r}")

    expected_path = ROOT / "src/main/java" / Path(*package.split(".")) / f"{src.stem}.java"
    if src != expected_path:
        raise ValueError(f"{src} does not match its package declaration {package!r}")

    return package.replace(".", "/"), src.stem, mod_id


# --------------------------------------------------------------------------
# Minimal Java class file writer
# --------------------------------------------------------------------------
class ConstantPool:
    """Deduplicating constant pool builder (no Long/Double entries needed)."""

    def __init__(self) -> None:
        self._entries: list[bytes] = []
        self._index: dict[tuple, int] = {}

    def _add(self, key: tuple, payload: bytes) -> int:
        if key in self._index:
            return self._index[key]
        idx = len(self._entries) + 1
        self._index[key] = idx
        self._entries.append(payload)
        return idx

    def utf8(self, value: str) -> int:
        raw = value.encode("utf-8")
        return self._add(("utf8", value), b"\x01" + struct.pack(">H", len(raw)) + raw)

    def class_(self, name: str) -> int:
        name_idx = self.utf8(name)
        return self._add(("class", name), b"\x07" + struct.pack(">H", name_idx))

    def name_and_type(self, name: str, desc: str) -> int:
        n, d = self.utf8(name), self.utf8(desc)
        return self._add(("nat", name, desc), b"\x0c" + struct.pack(">HH", n, d))

    def methodref(self, owner: str, name: str, desc: str) -> int:
        c = self.class_(owner)
        nt = self.name_and_type(name, desc)
        return self._add(("methodref", owner, name, desc), b"\x0a" + struct.pack(">HH", c, nt))

    def render(self) -> bytes:
        return struct.pack(">H", len(self._entries) + 1) + b"".join(self._entries)


def build_class(package_path: str, class_name: str, mod_id: str) -> bytes:
    """Emit the equivalent of: @Mod("mod_id") public class SpaceCraft { public SpaceCraft() {} }"""
    cp = ConstantPool()
    this_class = cp.class_(f"{package_path}/{class_name}")
    super_class = cp.class_("java/lang/Object")
    init_name = cp.utf8("<init>")
    init_desc = cp.utf8("()V")
    code_name = cp.utf8("Code")
    object_init = cp.methodref("java/lang/Object", "<init>", "()V")
    rva_name = cp.utf8("RuntimeVisibleAnnotations")
    annotation_type = cp.utf8(MOD_ANNOTATION_DESC)
    value_name = cp.utf8("value")
    value_const = cp.utf8(mod_id)
    sourcefile_name = cp.utf8("SourceFile")
    sourcefile_value = cp.utf8(f"{class_name}.java")

    # public <init>()V: aload_0; invokespecial Object.<init>; return
    code = b"\x2a" + b"\xb7" + struct.pack(">H", object_init) + b"\xb1"
    code_body = struct.pack(">HHI", 1, 1, len(code)) + code + struct.pack(">HH", 0, 0)
    method = (
        struct.pack(">HHHH", ACC_PUBLIC, init_name, init_desc, 1)
        + struct.pack(">HI", code_name, len(code_body))
        + code_body
    )

    # @Mod(value = "spacecraft") as a runtime-visible class annotation
    annotation = (
        struct.pack(">HH", annotation_type, 1)  # type_index, num_element_value_pairs
        + struct.pack(">H", value_name)         # element_name_index
        + b"s"                                  # element_value tag: string
        + struct.pack(">H", value_const)        # const_value_index
    )
    rva_body = struct.pack(">H", 1) + annotation
    src_body = struct.pack(">H", sourcefile_value)
    class_attributes = (
        struct.pack(">HI", rva_name, len(rva_body)) + rva_body
        + struct.pack(">HI", sourcefile_name, len(src_body)) + src_body
    )

    return (
        MAGIC
        + struct.pack(">HH", 0, MAJOR_VERSION)
        + cp.render()
        + struct.pack(">HHHHH", ACC_PUBLIC | ACC_SUPER, this_class, super_class, 0, 0)
        + struct.pack(">H", 1) + method
        + struct.pack(">H", 2) + class_attributes
    )


# --------------------------------------------------------------------------
# JAR contents
# --------------------------------------------------------------------------
def build_timestamp() -> datetime:
    """Honour SOURCE_DATE_EPOCH so repeated builds are byte-for-byte identical."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    return datetime.fromtimestamp(int(epoch), timezone.utc) if epoch else datetime.now(timezone.utc)


def build_manifest(props: dict[str, str], now: datetime) -> bytes:
    lines = [
        "Manifest-Version: 1.0",
        f"Specification-Title: {props['mod_id']}",
        f"Specification-Vendor: {props['mod_authors']}",
        "Specification-Version: 1",
        f"Implementation-Title: {ROOT.name}",
        f"Implementation-Version: {props['mod_version']}",
        f"Implementation-Vendor: {props['mod_authors']}",
        f"Implementation-Timestamp: {now.strftime('%Y-%m-%dT%H:%M:%S+0000')}",
    ]
    for line in lines:
        if len(line.encode("utf-8")) > 72:
            raise ValueError(f"MANIFEST line exceeds 72 bytes (needs continuation): {line!r}")
    return ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8")


def expected_entry_names(package_path: str, class_name: str) -> set[str]:
    return {
        "META-INF/",
        "META-INF/MANIFEST.MF",
        "META-INF/mods.toml",
        "pack.mcmeta",
        f"{package_path}/",
        f"{package_path}/{class_name}.class",
    }


def write_jar(
    out: Path,
    props: dict[str, str],
    package_path: str,
    class_name: str,
    mod_id: str,
    now: datetime,
) -> None:
    mods_toml = expand((ROOT / "src/main/resources/META-INF/mods.toml").read_text("utf-8"), props)
    pack_mcmeta = expand((ROOT / "src/main/resources/pack.mcmeta").read_text("utf-8"), props)
    dos_time = (now.year, now.month, now.day, now.hour, now.minute, now.second // 2 * 2)

    def entry(jar: zipfile.ZipFile, name: str, payload: bytes) -> None:
        info = zipfile.ZipInfo(name, date_time=dos_time)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o755 if name.endswith("/") else 0o644) << 16
        jar.writestr(info, payload)

    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w") as jar:
        entry(jar, "META-INF/", b"")
        entry(jar, "META-INF/MANIFEST.MF", build_manifest(props, now))
        entry(jar, "META-INF/mods.toml", mods_toml.encode("utf-8"))
        entry(jar, "pack.mcmeta", pack_mcmeta.encode("utf-8"))
        entry(jar, f"{package_path}/", b"")
        entry(jar, f"{package_path}/{class_name}.class", build_class(package_path, class_name, mod_id))
    tmp.replace(out)


# --------------------------------------------------------------------------
# Verification
# --------------------------------------------------------------------------
class Reader:
    def __init__(self, data: bytes) -> None:
        self.data, self.pos = data, 0

    def u1(self) -> int:
        value = self.data[self.pos]
        self.pos += 1
        return value

    def u2(self) -> int:
        value = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return value

    def u4(self) -> int:
        value = struct.unpack_from(">I", self.data, self.pos)[0]
        self.pos += 4
        return value

    def take(self, n: int) -> bytes:
        value = self.data[self.pos:self.pos + n]
        self.pos += n
        return value


def parse_class(data: bytes) -> dict:
    """Parse enough of a .class file to prove Forge can find the @Mod entry point."""
    r = Reader(data)
    if r.take(4) != MAGIC:
        raise ValueError("Bad class file magic")
    minor, major = r.u2(), r.u2()
    if major != MAJOR_VERSION or minor != 0:
        raise ValueError(f"Expected Java 17 class version 61.0, got {major}.{minor}")

    count = r.u2()
    cp: list = [None] * count
    i = 1
    while i < count:
        tag = r.u1()
        if tag == 1:  # Utf8
            cp[i] = ("utf8", r.take(r.u2()).decode("utf-8"))
        elif tag in (7, 8, 16, 19, 20):  # Class, String, MethodType, Module, Package
            cp[i] = (tag, r.u2())
        elif tag in (9, 10, 11, 12, 17, 18):  # refs, NameAndType, Dynamic, InvokeDynamic
            cp[i] = (tag, r.u2(), r.u2())
        elif tag in (3, 4):  # Integer, Float
            cp[i] = (tag, r.take(4))
        elif tag in (5, 6):  # Long, Double occupy two slots
            cp[i] = (tag, r.take(8))
            i += 1
        elif tag == 15:  # MethodHandle
            cp[i] = (tag, r.u1(), r.u2())
        else:
            raise ValueError(f"Unsupported constant pool tag {tag} at index {i}")
        i += 1

    def utf8(idx: int) -> str:
        entry = cp[idx]
        if not entry or entry[0] != "utf8":
            raise ValueError(f"Constant pool #{idx} is not a Utf8")
        return entry[1]

    def read_attributes(reader: Reader) -> list[tuple[str, bytes]]:
        result = []
        for _ in range(reader.u2()):
            name = utf8(reader.u2())
            length = reader.u4()
            result.append((name, reader.take(length)))
        return result

    access = r.u2()
    this_name = utf8(cp[r.u2()][1])
    super_name = utf8(cp[r.u2()][1])
    for _ in range(r.u2()):  # interfaces
        r.u2()
    for _ in range(r.u2()):  # fields
        r.u2(); r.u2(); r.u2(); read_attributes(r)

    methods = []
    for _ in range(r.u2()):
        m_access, m_name, m_desc = r.u2(), utf8(r.u2()), utf8(r.u2())
        m_attrs = read_attributes(r)
        methods.append((m_access, m_name, m_desc, [a[0] for a in m_attrs]))
    class_attrs = read_attributes(r)
    if r.pos != len(data):
        raise ValueError(f"class file has {len(data) - r.pos} unexpected trailing bytes")

    annotations = []
    for name, body in class_attrs:
        if name != "RuntimeVisibleAnnotations":
            continue
        ar = Reader(body)
        for _ in range(ar.u2()):
            atype = utf8(ar.u2())
            pairs = {}
            for _ in range(ar.u2()):
                key = utf8(ar.u2())
                tag = chr(ar.u1())
                if tag == "s":
                    pairs[key] = utf8(ar.u2())
                elif tag in "BCDFIJSZc":
                    pairs[key] = ("constant", ar.u2())
                elif tag == "e":
                    pairs[key] = ("enum", utf8(ar.u2()), utf8(ar.u2()))
                else:
                    raise ValueError(f"Unsupported element_value tag {tag!r}")
            annotations.append((atype, pairs))

    return {
        "major": major,
        "access": access,
        "class": this_name,
        "super": super_name,
        "methods": methods,
        "attributes": [a[0] for a in class_attrs],
        "annotations": annotations,
    }


def verify_jar(out: Path, props: dict[str, str], package_path: str, class_name: str) -> dict:
    with zipfile.ZipFile(out) as jar:
        broken = jar.testzip()
        if broken:
            raise ValueError(f"Corrupt ZIP entry: {broken}")
        names = set(jar.namelist())
        expected = expected_entry_names(package_path, class_name)
        if names != expected:
            raise ValueError(f"Unexpected JAR entries.\n  missing: {sorted(expected - names)}\n  extra: {sorted(names - expected)}")

        mods = tomllib.loads(jar.read("META-INF/mods.toml").decode("utf-8"))
        pack = json.loads(jar.read("pack.mcmeta").decode("utf-8"))
        manifest = jar.read("META-INF/MANIFEST.MF").decode("utf-8")
        class_data = jar.read(f"{package_path}/{class_name}.class")

    if mods.get("modLoader") != "javafml":
        raise ValueError("mods.toml: modLoader must be javafml")
    if mods.get("loaderVersion") != props["loader_version_range"]:
        raise ValueError("mods.toml: loaderVersion does not match gradle.properties")
    if not mods.get("license"):
        raise ValueError("mods.toml: license is mandatory")
    mod = mods["mods"][0]
    if mod["modId"] != props["mod_id"] or mod["version"] != props["mod_version"]:
        raise ValueError("mods.toml: modId/version do not match gradle.properties")
    deps = {d["modId"]: d for d in mods["dependencies"][props["mod_id"]]}
    if set(deps) != {"forge", "minecraft"}:
        raise ValueError(f"mods.toml: expected forge + minecraft dependencies, got {sorted(deps)}")
    if deps["forge"]["versionRange"] != props["forge_version_range"]:
        raise ValueError("mods.toml: forge versionRange mismatch")
    if deps["minecraft"]["versionRange"] != props["minecraft_version_range"]:
        raise ValueError("mods.toml: minecraft versionRange mismatch")

    if pack["pack"]["pack_format"] != int(props["pack_format_number"]):
        raise ValueError("pack.mcmeta: pack_format mismatch")

    if f"Implementation-Version: {props['mod_version']}" not in manifest:
        raise ValueError("MANIFEST.MF: Implementation-Version mismatch")

    info = parse_class(class_data)
    if info["class"] != f"{package_path}/{class_name}" or info["super"] != "java/lang/Object":
        raise ValueError("class: unexpected this/super class")
    if not (info["access"] & ACC_PUBLIC):
        raise ValueError("class: entry point must be public")
    if ("<init>", "()V", ["Code"]) not in [(m[1], m[2], m[3]) for m in info["methods"]]:
        raise ValueError("class: missing public no-arg constructor")
    mod_annotations = [a for a in info["annotations"] if a[0] == MOD_ANNOTATION_DESC]
    if len(mod_annotations) != 1 or mod_annotations[0][1].get("value") != props["mod_id"]:
        raise ValueError("class: @Mod(\"<mod_id>\") runtime-visible annotation missing")

    return {
        "jar": str(out.relative_to(ROOT)),
        "size": out.stat().st_size,
        "entries": sorted(names),
        "mod": mod,
        "deps": deps,
        "pack_format": pack["pack"]["pack_format"],
        "class": info,
    }


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, help="output JAR path (default: dist/<mod_id>-<mod_version>.jar)")
    ap.add_argument("--check", action="store_true", help="verify an existing JAR without rebuilding")
    args = ap.parse_args()

    props = read_properties(ROOT / "gradle.properties")
    package_path, class_name, mod_id = find_entry_point(props)
    out = (args.out or ROOT / "dist" / f"{props['mod_id']}-{props['mod_version']}.jar").resolve()

    if not args.check:
        write_jar(out, props, package_path, class_name, mod_id, build_timestamp())
    result = verify_jar(out, props, package_path, class_name)

    action = "Verified" if args.check else "Built"
    print(f"{action}: {result['jar']}  ({result['size']} bytes)")
    print(f"  Minecraft  : {props['minecraft_version']} / Forge {props['forge_version']}")
    print(f"  modId      : {result['mod']['modId']}  version {result['mod']['version']}")
    print(f"  loader     : javafml {props['loader_version_range']}")
    print(f"  deps       : " + ", ".join(f"{k} {v['versionRange']}" for k, v in result["deps"].items()))
    print(f"  pack_format: {result['pack_format']}")
    print(f"  class      : {result['class']['class']} (Java {result['class']['major']}, @Mod(\"{mod_id}\"))")
    print("  entries    :")
    for name in result["entries"]:
        print(f"    - {name}")
    print("OK: this JAR is loadable by Forge 1.20.1 and registers nothing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
