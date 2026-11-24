#!/usr/bin/env python3
"""アイテムの **3D モデル・テクスチャ・一覧用 3D 画像**を生成する（標準ライブラリのみ）。

    python3 tools/itemart.py wrench

生成物（すべて同じ `MODEL_DEFS` と同じ 16x16 パレットテクスチャ由来）:

    src/main/resources/assets/spacecraft/models/item/<id>.json   … ゲームに読み込まれる 3D モデル
    src/main/resources/assets/spacecraft/textures/item/<id>.png  … 面の色を決める 16x16 テクスチャ
    アイテム一覧/models/<id>.json                                … 上記モデルの説明用の写し
    アイテム一覧/images/<id>_3d.svg                              … 単体の 3D 全体図
    アイテム一覧/images/<id>_inventory.svg                       … スロット内の 3D
    アイテム一覧/images/<id>_held.svg                            … 手に持った 3D

**これから追加するアイテムはすべて 3D です。** 2D のスプライト（`item/generated` の
layer0 だけ）には戻さないでください。新しいアイテムは `MODEL_DEFS` に `elements` を
足すだけで、ゲーム内モデルと 3 枚の画像が同時に更新されます。

3D の描画そのものは `tools/model3d.py` にあります（catalog.py と共用）。
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zlib
from pathlib import Path

from model3d import bounds, document, place, scene

ROOT = Path(__file__).resolve().parents[1]
ITEM_LIST = ROOT / "アイテム一覧"
ASSET_MODELS = ROOT / "src/main/resources/assets/spacecraft/models/item"
ASSET_TEXTURES = ROOT / "src/main/resources/assets/spacecraft/textures/item"
ID_RE = re.compile(r"^[a-z0-9_]+$")

# 16x16 パレット（象限ごとに面の役割を割り当てる）
LIGHT = (214, 223, 233, 255)  # 上面
METAL = (150, 163, 178, 255)  # 側面
DARK = (75, 86, 102, 255)    # 下面・影
GRIP = (56, 68, 82, 255)     # グリップ
CYAN = (79, 209, 197, 255)   # 宇宙クラフトのアクセント（グリップ端面）

UV_LIGHT = (0, 0, 8, 8)
UV_METAL = (8, 0, 16, 8)
UV_DARK = (0, 8, 8, 16)
UV_GRIP = (8, 8, 16, 16)
UV_ACCENT = (10, 10, 14, 14)


def png_bytes(px: list[list[tuple[int, int, int, int]]]) -> bytes:
    """RGBA PNG を標準ライブラリだけで書き出す（filter 0 固定）。"""
    height, width = len(px), len(px[0])
    raw = bytearray()
    for row in px:
        raw.append(0)
        for r, g, b, a in row:
            raw += bytes((r, g, b, a))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def palette_texture() -> bytes:
    px = [[LIGHT for _ in range(16)] for _ in range(16)]
    for y in range(16):
        for x in range(16):
            if x < 8 and y < 8:
                px[y][x] = LIGHT
            elif x >= 8 and y < 8:
                px[y][x] = METAL
            elif x < 8 and y >= 8:
                px[y][x] = DARK
            else:
                px[y][x] = GRIP
    # 右下象限の一部を差し色に（グリップ端面の uv がここを指す）
    for y in range(10, 15):
        for x in range(10, 15):
            px[y][x] = CYAN
    return png_bytes(px)


def box(x0, y0, z0, x1, y1, z1, *, up=UV_LIGHT, side=UV_METAL, down=UV_DARK, accent=None) -> dict:
    """1 つの直方体 element。6 面すべてに uv を付けてテクスチャと一致させる。"""
    uvs = {"up": up, "down": down, "north": side, "south": side, "west": side, "east": side}
    if accent:
        uvs["east"] = accent  # +x 側の端面
    return {
        "from": [x0, y0, z0],
        "to": [x1, y1, z1],
        "faces": {name: {"texture": "#0", "uv": list(uv)} for name, uv in uvs.items()},
    }


def wrench_model() -> dict:
    """横に寝かせたレンチ。柄・グリップ・U 字の開口を 5 つの直方体で構成する。"""
    return {
        "parent": "block/block",
        "textures": {
            "0": "spacecraft:item/wrench",
            "particle": "spacecraft:item/wrench",
        },
        "elements": [
            box(4, 7, 7, 12, 9, 9),                                          # 柄
            box(11, 6, 5, 15, 10, 11, up=UV_GRIP, side=UV_GRIP, accent=UV_ACCENT),  # グリップ
            box(0, 10, 7, 4, 12, 9),                                         # 開口・上あご
            box(0, 4, 7, 4, 6, 9),                                           # 開口・下あご
            box(0, 6, 7, 2, 10, 9),                                          # 開口・背
        ],
        "display": {
            "gui": {"rotation": [30, 225, 0], "translation": [0, 0, 0], "scale": [0.7, 0.7, 0.7]},
            "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [0.35, 0.35, 0.35]},
            "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 4, 0.5], "scale": [0.85, 0.85, 0.85]},
            "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 4, 0.5], "scale": [0.85, 0.85, 0.85]},
            "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
            "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
        },
    }


MODEL_DEFS = {"wrench": wrench_model()}
IMAGE_KINDS = ("_3d", "_inventory", "_held")


def centered(model: Path, palette: Path, *, yaw, pitch, scale, cx, cy) -> tuple[list[str], float, float]:
    polys, _ = scene(model, yaw=yaw, pitch=pitch, scale=scale, palette_path=palette)
    minx, miny, maxx, maxy = bounds(polys)
    ox = cx - (minx + maxx) / 2
    oy = cy - (miny + maxy) / 2
    return place(polys, ox, oy), maxx - minx, maxy - miny


def build_images(model: Path, palette: Path, id_: str) -> dict[str, str]:
    out: dict[str, str] = {}

    # 1) 単体の 3D 全体図
    body, _, _ = centered(model, palette, yaw=45, pitch=32, scale=14, cx=170, cy=132)
    stars = [
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#4fd1c5" opacity="0.5"/>'
        for x, y, r in ((36, 38, 1.6), (292, 52, 1.8), (56, 208, 1.1), (270, 210, 1.3))
    ]
    out["_3d"] = document(
        340, 280, body,
        f"spacecraft:{id_} — 3D モデル（models/{id_}.json 由来）",
        background=stars, label_y=262,
    )

    # 2) インベントリスロット内の 3D
    body, _, _ = centered(model, palette, yaw=45, pitch=30, scale=8.5, cx=120, cy=96)
    slot = [
        '<rect x="48" y="24" width="144" height="144" fill="#8b8b8b" stroke="#373737" stroke-width="4"/>',
        '<path d="M52 28 L188 28 L52 164 Z" fill="#ffffff" opacity="0.12"/>',
        '<path d="M188 28 L188 164 L52 164 Z" fill="#000000" opacity="0.18"/>',
    ]
    out["_inventory"] = document(
        240, 230, body,
        f"spacecraft:{id_} — インベントリ内の状態（3D）",
        background=slot, label_y=210,
    )

    # 3) 手に持った 3D（視点を変えて斜めに構える）
    body, _, _ = centered(model, palette, yaw=22, pitch=24, scale=11, cx=150, cy=122)
    hand = [
        '<circle cx="40" cy="36" r="1.6" fill="#4fd1c5" opacity="0.55"/>',
        '<circle cx="278" cy="48" r="1.8" fill="#4fd1c5" opacity="0.55"/>',
        '<circle cx="296" cy="120" r="1.2" fill="#4fd1c5" opacity="0.45"/>',
        '<path d="M214 260 L232 170 L286 182 L306 260 Z" fill="#b9805c"/>',
        '<path d="M232 170 L286 182 L280 200 L228 188 Z" fill="#d69a72"/>',
    ]
    out["_held"] = document(
        320, 260, body,
        f"spacecraft:{id_} — 手に持った状態（3D）",
        background=hand, label_y=242,
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id", help=f"アイテム id（現在: {', '.join(MODEL_DEFS)}）")
    args = ap.parse_args()

    if not ID_RE.match(args.id):
        print("エラー: id は半角英小文字・数字・アンダースコアのみ", file=sys.stderr)
        return 1
    if args.id not in MODEL_DEFS:
        print(f"エラー: {args.id} の 3D モデル定義がありません（tools/itemart.py の MODEL_DEFS に追加してください）", file=sys.stderr)
        return 1

    model_json = json.dumps(MODEL_DEFS[args.id], indent=2, ensure_ascii=False) + "\n"
    texture = ASSET_TEXTURES / f"{args.id}.png"
    asset_model = ASSET_MODELS / f"{args.id}.json"
    list_model = ITEM_LIST / "models" / f"{args.id}.json"

    for path in (texture, asset_model, list_model):
        path.parent.mkdir(parents=True, exist_ok=True)
    texture.write_bytes(palette_texture())
    asset_model.write_text(model_json, encoding="utf-8")
    list_model.write_text(model_json, encoding="utf-8")

    images = build_images(list_model, texture, args.id)
    for kind, svg in images.items():
        path = ITEM_LIST / "images" / f"{args.id}{kind}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")

    for path in (asset_model, texture, list_model):
        print(f"生成: {path.relative_to(ROOT)}  ({path.stat().st_size} bytes)")
    for kind in IMAGE_KINDS:
        path = ITEM_LIST / "images" / f"{args.id}{kind}.svg"
        print(f"生成: {path.relative_to(ROOT)}  ({path.stat().st_size} bytes)")
    print("      3 枚の画像はすべて同じ 3D モデル JSON とテクスチャから組み立てています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
