#!/usr/bin/env python3
"""一覧ドキュメントの管理ツール（ビルド不要・外部依存なし・標準ライブラリのみ）。

このスクリプトは mod のビルドには一切関係しません。5 つの一覧
（アイテム / block / Ui / 装備 / エンティティ）の md と画像を管理します。

使い方:
    python3 tools/catalog.py list                      登録状況を表示
    python3 tools/catalog.py check                     整合性を検証
    python3 tools/catalog.py check --strict            画像未配置もエラーにする
    python3 tools/catalog.py new <一覧> <id>           _template.md から <id>.md を作成
    python3 tools/catalog.py render <一覧> <id>        models/<id>.json -> images/<id>_3d.svg
    python3 tools/catalog.py render <一覧> x --example 見本 JSON から 3D SVG を生成

一覧名は日本語でそのまま指定します（例: "block一覧"、"エンティティ一覧（スポーンエッグに限る）"）。
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 一覧名 -> 必須画像の接尾辞 / モデル JSON が必要か
CATEGORIES: dict[str, dict] = {
    "アイテム一覧": {
        "images": ["_inventory", "_held"],
        "model": False,
    },
    "block一覧": {
        "images": ["_3d"],
        "model": True,
    },
    "Ui一覧": {
        "images": ["_ui"],
        "model": False,
    },
    "装備一覧": {
        "images": ["_held", "_inventory", "_equipped"],
        "model": True,
    },
    "エンティティ一覧（スポーンエッグに限る）": {
        "images": ["_egg", "_3d", "_egg_held"],
        "model": False,
    },
}

ID_RE = re.compile(r"^[a-z0-9_]+$")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".svg", ".webp")


def cat_dir(name: str) -> Path:
    return ROOT / name


def entry_files(name: str) -> list[Path]:
    """一覧に登録された要素の md（README / _ で始まる雛形は除く）。"""
    d = cat_dir(name)
    if not d.is_dir():
        return []
    return sorted(
        p for p in d.glob("*.md")
        if p.name != "README.md" and not p.name.startswith("_")
    )


def find_image(d: Path, stem: str, suffix: str) -> Path | None:
    for ext in IMAGE_EXT:
        candidate = d / "images" / f"{stem}{suffix}{ext}"
        if candidate.is_file():
            return candidate
    return None


# --------------------------------------------------------------------------
# list
# --------------------------------------------------------------------------
def cmd_list() -> int:
    total = 0
    for name, cfg in CATEGORIES.items():
        mds = entry_files(name)
        total += len(mds)
        print(f"■ {name}  （{len(mds)} 件）")
        if not mds:
            print("   （未登録 — 実装済みの要素はまだありません）")
        for md in mds:
            status = []
            for suffix in cfg["images"]:
                found = find_image(cat_dir(name), md.stem, suffix)
                status.append(f"{suffix}={'OK' if found else '未配置'}")
            print(f"   - {md.name}   " + "  ".join(status))
        print()
    print(f"合計 {total} 件 / 5 一覧")
    return 0


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------
def cmd_check(strict: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for name, cfg in CATEGORIES.items():
        d = cat_dir(name)
        if not d.is_dir():
            errors.append(f"[{name}] ディレクトリがありません")
            continue
        for required in ("ここに追加", "README.md", "_template.md"):
            if not (d / required).exists():
                errors.append(f"[{name}] {required} がありません（ユーザー作成のプレースホルダ / 雛形は残してください）")
        if not (d / "images").is_dir():
            errors.append(f"[{name}] images/ がありません")

        # 見本 JSON の構文
        for example in sorted(d.glob("_example*.json")):
            try:
                json.loads(example.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"[{name}] {example.name} の JSON が不正: {exc}")

        for md in entry_files(name):
            stem = md.stem
            text = md.read_text(encoding="utf-8")
            if not ID_RE.match(stem):
                errors.append(f"[{name}] {md.name}: id は半角英小文字・数字・_ のみ")
            if "<id>" in text:
                errors.append(f"[{name}] {md.name}: <id> プレースホルダが残っています")

            for suffix in cfg["images"]:
                found = find_image(d, stem, suffix)
                if not found:
                    msg = f"[{name}] {md.name}: 画像 {stem}{suffix}.png が未配置"
                    (errors if strict else warnings).append(msg)
                elif f"](images/{found.name})" not in text:
                    warnings.append(f"[{name}] {md.name}: {found.name} はあるのに md から参照されていません（画像コメントを外してください）")

            if cfg["model"]:
                model = d / "models" / f"{stem}.json"
                if not model.exists():
                    msg = f"[{name}] {md.name}: models/{stem}.json がありません"
                    (errors if strict else warnings).append(msg)
                else:
                    try:
                        json.loads(model.read_text(encoding="utf-8"))
                    except json.JSONDecodeError as exc:
                        errors.append(f"[{name}] {model.name} の JSON が不正: {exc}")

            readme = (d / "README.md")
            if readme.exists() and stem not in readme.read_text(encoding="utf-8"):
                warnings.append(f"[{name}] {md.name}: README.md の表に 1 行追加してください")

    for line in warnings:
        print(f"警告: {line}")
    for line in errors:
        print(f"エラー: {line}")

    if errors:
        print(f"\n検証結果: エラー {len(errors)} 件 / 警告 {len(warnings)} 件")
        return 1
    print(f"OK: 5 一覧の構造に問題ありません（エラー 0 件 / 警告 {len(warnings)} 件）")
    if warnings and not strict:
        print("    画像・モデルは要素を実装したときに配置してください。厳密に確認する場合は --strict を付けてください。")
    return 0


# --------------------------------------------------------------------------
# new
# --------------------------------------------------------------------------
def cmd_new(category: str, id_: str) -> int:
    if category not in CATEGORIES:
        print(f"エラー: 一覧名が不正です。次から選んでください: {', '.join(CATEGORIES)}", file=sys.stderr)
        return 1
    if not ID_RE.match(id_):
        print("エラー: id は半角英小文字・数字・アンダースコアのみ（例: moon_rock）", file=sys.stderr)
        return 1

    d = cat_dir(category)
    template = d / "_template.md"
    target = d / f"{id_}.md"
    if not template.exists():
        print(f"エラー: {template} がありません", file=sys.stderr)
        return 1
    if target.exists():
        print(f"エラー: {target.name} は既に存在します", file=sys.stderr)
        return 1

    # <id> だけ機械的に置換。それ以外の <...> は人が埋める。
    target.write_text(template.read_text(encoding="utf-8").replace("<id>", id_), encoding="utf-8")

    # README.md の表に 1 行追加（空の「| — | ...」行を置換、無ければ表の末尾に追加）
    readme = d / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines()
    cells = [f"`{id_}`", "<日本語名>", f"[`{id_}.md`]({id_}.md)", "未実装"]
    placeholder = next((i for i, line in enumerate(lines) if line.startswith("| — |")), None)
    if placeholder is not None:
        column_count = lines[placeholder].count("|") - 1
        if column_count == 5:  # 装備・エンティティは列が 1 つ多い
            cells.insert(2, "—")
        lines[placeholder] = "| " + " | ".join(cells) + " |"
    else:
        column_count = 5 if category in ("装備一覧", "エンティティ一覧（スポーンエッグに限る）") else 4
        if column_count == 5:
            cells.insert(2, "—")
        last_row = max((i for i, line in enumerate(lines) if line.startswith("|")), default=None)
        if last_row is None:
            warnings_line = "表が見つかりませんでした。README.md に手動で追記してください。"
            print(f"警告: {warnings_line}")
        else:
            lines.insert(last_row + 1, "| " + " | ".join(cells) + " |")
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"作成: {target.relative_to(ROOT)}  （{readme.relative_to(ROOT)} にも 1 行追加）")
    print("次に: <...> を埋め、画像を images/ に置き、md の画像コメントを外してください。ビルドは不要です。")
    return 0


# --------------------------------------------------------------------------
# render: モデル JSON -> 等角投影の 3D SVG
# --------------------------------------------------------------------------
def project(x: float, y: float, z: float, scale: float = 12.0) -> tuple[float, float]:
    """Minecraft 座標 (0..16) を等角投影の画面座標へ。"""
    rad = math.radians(30)
    return (x - z) * math.cos(rad) * scale, (x + z) * math.sin(rad) * scale - y * scale


def render_svg(model_path: Path, out_path: Path, title: str) -> str:
    data = json.loads(model_path.read_text(encoding="utf-8"))
    elements = data.get("elements")
    note = ""
    if not elements:
        # item/handheld のように display だけのモデルは既定の立方体を描く
        elements = [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": {}}]
        note = "（elements が無いため既定の立方体を描画しました）"

    polygons: list[tuple[float, str, list[tuple[float, float]]]] = []
    for element in elements:
        x0, y0, z0 = element["from"]
        x1, y1, z1 = element["to"]
        depth = (x0 + x1) / 2 + (y0 + y1) / 2 + (z0 + z1) / 2
        faces = [
            ("#c3ced9", [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]),  # up
            ("#8592a1", [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]),  # east
            ("#626d7c", [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),  # south
        ]
        for color, points in faces:
            polygons.append((depth, color, [project(*p) for p in points]))
    polygons.sort(key=lambda item: item[0])  # 奥から手前へ

    all_points = [p for _, _, pts in polygons for p in pts]
    min_x, max_x = min(p[0] for p in all_points), max(p[0] for p in all_points)
    min_y, max_y = min(p[1] for p in all_points), max(p[1] for p in all_points)
    pad_x, pad_top, pad_bottom = 40, 40, 54
    width = int(max_x - min_x + pad_x * 2)
    height = int(max_y - min_y + pad_top + pad_bottom)
    off_x, off_y = -min_x + pad_x, -min_y + pad_top

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)} の 3D モデル">',
        f'<rect width="100%" height="100%" fill="#15181e" rx="8"/>',
    ]
    for _, color, pts in polygons:
        coords = " ".join(f"{x + off_x:.2f},{y + off_y:.2f}" for x, y in pts)
        svg.append(f'  <polygon points="{coords}" fill="{color}" stroke="#2b3038" stroke-width="1.2"/>')
    svg.append(
        f'  <text x="{width / 2:.0f}" y="{height - 20:.0f}" fill="#c9d1d9" '
        f'font-family="sans-serif" font-size="13" text-anchor="middle">{html.escape(title)}</text>'
    )
    svg.append("</svg>")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(svg) + "\n", encoding="utf-8")
    return note


def cmd_render(category: str, id_: str, example: bool) -> int:
    if category not in CATEGORIES:
        print(f"エラー: 一覧名が不正です。次から選んでください: {', '.join(CATEGORIES)}", file=sys.stderr)
        return 1
    d = cat_dir(category)
    stem = "_example" if example else id_
    model = d / "_example_model.json" if example else d / "models" / f"{stem}.json"
    out = d / "images" / f"{stem}_3d.svg"
    if not model.exists():
        print(f"エラー: {model.relative_to(ROOT)} がありません", file=sys.stderr)
        return 1

    note = render_svg(model, out, f"spacecraft:{stem}")
    print(f"生成: {out.relative_to(ROOT)}  ← {model.relative_to(ROOT)}")
    if note:
        print(f"      {note}")
    print("      SVG はテキストなので外部ライブラリ不要です。md から images/xxx_3d.svg を参照してください。")
    return 0


# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="5 一覧の登録状況を表示")
    p_check = sub.add_parser("check", help="一覧の構造・JSON・画像参照を検証")
    p_check.add_argument("--strict", action="store_true", help="画像・モデル未配置もエラーにする")
    p_new = sub.add_parser("new", help="_template.md から新しい <id>.md を作成")
    p_new.add_argument("category", help="一覧名（日本語）")
    p_new.add_argument("id", help="登録 id（半角英小文字・数字・_）")
    p_render = sub.add_parser("render", help="モデル JSON から 3D SVG を生成")
    p_render.add_argument("category", help="一覧名（日本語）")
    p_render.add_argument("id", help="登録 id（--example のときは任意の文字列で可）")
    p_render.add_argument("--example", action="store_true", help="_example_model.json を見本として描く")

    args = parser.parse_args()
    if args.command == "list":
        return cmd_list()
    if args.command == "check":
        return cmd_check(args.strict)
    if args.command == "new":
        return cmd_new(args.category, args.id)
    if args.command == "render":
        return cmd_render(args.category, args.id, args.example)
    return 1


if __name__ == "__main__":
    sys.exit(main())
