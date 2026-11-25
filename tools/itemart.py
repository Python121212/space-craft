#!/usr/bin/env python3
"""`画像/` の見本テクスチャから **3D モデル・実テクスチャ・一覧用 3D 画像**を生成する。

    python3 tools/itemart.py wrench

**`画像/` はユーザーが「こんなテクスチャにして」という見本を置く場所**です。
ここに置かれた PNG を唯一の source として、次を一括生成します（標準ライブラリのみ）:

    src/main/resources/assets/spacecraft/textures/item/<id>.png  … 見本を 64x64 に落とした実テクスチャ
    src/main/resources/assets/spacecraft/models/item/<id>.json   … ゲームに読み込まれる 3D モデル
    アイテム一覧/models/<id>.json                                … 上記モデルの説明用の写し
    アイテム一覧/images/<id>_3d.svg                              … 単体の 3D 全体図
    アイテム一覧/images/<id>_inventory.svg                       … スロット内の 3D
    アイテム一覧/images/<id>_held.svg                            … 手に持った 3D

## テクスチャを「見本のように」保つ工夫

- 見本は **256x256 = 16x16 ドット絵の 16 倍拡大**ですが、1 セル 1 色に量子化すると
  銀のグラデーションが失われます。そのため **64x64（4 倍の解像度）へエリア平均**で
  ダウンサンプルし、見本の 40 色の階調をできるだけ残します。
- 白背景は「非白ピクセルの割合」でアルファを決めるため、輪郭が白くにじまず
  アンチエイリアスも再現されます（真っ白な背景だけ完全透過）。
- 3D モデルの各面 `faces.uv` は **64x64 テクスチャ上の 1 テクセル**を指します。
  `tools/model3d.py` は uv 矩形の平均色で面を塗るため、1 テクセルなら見本の実色を
  そのまま、広い矩形なら階調を含めた平均色を 3D 画像へ反映できます。

見本 PNG はインデックスカラー / RGB / RGBA / 透過 / 全 PNG filter に対応しています
（`tools/model3d.py` の read_png）。
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zlib
from pathlib import Path

from model3d import bounds, document, place, read_png, scene

ROOT = Path(__file__).resolve().parents[1]
ITEM_LIST = ROOT / "アイテム一覧"
SOURCE_DIR = ROOT / "画像"
ASSET_MODELS = ROOT / "src/main/resources/assets/spacecraft/models/item"
ASSET_TEXTURES = ROOT / "src/main/resources/assets/spacecraft/textures/item"
ID_RE = re.compile(r"^[a-z0-9_]+$")

# 実テクスチャの解像度。見本 256x256 を 64x64 に落とす（1 テクセル = 4x4 元ピクセル）。
# Minecraft は 16x16 以外のアイテムテクスチャも読み込めます。
TEXTURE_SIZE = 64

# id -> `画像/` に置かれた見本テクスチャ
SOURCE_FILES = {
    "wrench": "IMG_809df39f-4a58-433f-b6f5-0b58e51e80d2.png",
}

# 64x64 テクスチャ上の **1 テクセル**（見本の代表色を点で拾う）
# 64x64 へエリア平均すると極小のハイライトが消えるため、面の色は 1 ピクセル uv で
# 見本の実色をそのまま指定します。明るさ順が上→側→別階調→下→輪郭になるよう選択済み。
# すべて不透明ピクセルなので、3D 画像が既定色にフォールバックしません。
UV_UP = (14, 46, 15, 47)       # #dedede 上面（最も明るい銀）
UV_SIDE = (14, 49, 15, 50)     # #c5c5c5 側面
UV_ACCENT = (12, 51, 13, 52)   # #a7a7a7 グリップの別階調
UV_DOWN = (49, 27, 50, 28)     # #9f9f9f 下面（影）
UV_OUTLINE = (7, 50, 8, 51)    # #282828 黒アウトライン


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


def source_texture(name: str) -> bytes:
    """見本を 64x64 へエリア平均でダウンサンプルし、白背景を段階的に透過する。"""
    src = SOURCE_DIR / name
    pal = read_png(src)
    if pal is None:
        raise FileNotFoundError(
            f"見本テクスチャを読み込めません: {src}（画像/ に 8bit PNG を置いてください）"
        )
    n = TEXTURE_SIZE
    px: list[list[tuple[int, int, int, int]]] = []
    for gy in range(n):
        row: list[tuple[int, int, int, int]] = []
        for gx in range(n):
            x0 = gx * pal.width // n
            x1 = max(x0 + 1, (gx + 1) * pal.width // n)
            y0 = gy * pal.height // n
            y1 = max(y0 + 1, (gy + 1) * pal.height // n)
            r = g = b = count = 0
            total = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    pr, pg, pb, _pa = pal.pixel(x, y)
                    total += 1
                    # 白に近い背景ピクセルは色の平均から除外する（白いフチを防ぐ）
                    if min(pr, pg, pb) >= 250:
                        continue
                    r += pr
                    g += pg
                    b += pb
                    count += 1
            if count:
                # 非白ピクセルの割合でアルファを決め、輪郭をアンチエイリアスする
                alpha = int(255 * count / total)
                row.append((r // count, g // count, b // count, alpha))
            else:
                row.append((255, 255, 255, 0))
        px.append(row)
    return png_bytes(px)


def box(x0, y0, z0, x1, y1, z1, *, up=UV_UP, side=UV_SIDE, down=UV_DOWN, accent=None) -> dict:
    """1 つの直方体 element。6 面すべてに実テクスチャの uv を付ける。"""
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
            box(4, 7, 7, 12, 9, 9),                                            # 柄
            box(11, 6, 5, 15, 10, 11, up=UV_SIDE, side=UV_ACCENT, accent=UV_OUTLINE),  # グリップ
            box(0, 10, 7, 4, 12, 9),                                           # 開口・上あご
            box(0, 4, 7, 4, 6, 9),                                             # 開口・下あご
            box(0, 6, 7, 2, 10, 9),                                            # 開口・背
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
STAR = "#8b949e"  # 見本画像のモノクロ配色に合わせた背景の星


def centered(model: Path, palette: Path, *, yaw, pitch, scale, cx, cy):
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
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{STAR}" opacity="0.5"/>'
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
        f'<circle cx="40" cy="36" r="1.6" fill="{STAR}" opacity="0.55"/>',
        f'<circle cx="278" cy="48" r="1.8" fill="{STAR}" opacity="0.55"/>',
        f'<circle cx="296" cy="120" r="1.2" fill="{STAR}" opacity="0.45"/>',
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
    if args.id not in SOURCE_FILES:
        print(f"エラー: {args.id} の見本テクスチャが 画像/ に登録されていません（SOURCE_FILES に追加してください）", file=sys.stderr)
        return 1

    try:
        texture_png = source_texture(SOURCE_FILES[args.id])
    except (FileNotFoundError, ValueError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    model_json = json.dumps(MODEL_DEFS[args.id], indent=2, ensure_ascii=False) + "\n"
    texture = ASSET_TEXTURES / f"{args.id}.png"
    asset_model = ASSET_MODELS / f"{args.id}.json"
    list_model = ITEM_LIST / "models" / f"{args.id}.json"

    for path in (texture, asset_model, list_model):
        path.parent.mkdir(parents=True, exist_ok=True)
    texture.write_bytes(texture_png)
    asset_model.write_text(model_json, encoding="utf-8")
    list_model.write_text(model_json, encoding="utf-8")

    images = build_images(list_model, texture, args.id)
    for kind, svg in images.items():
        path = ITEM_LIST / "images" / f"{args.id}{kind}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg, encoding="utf-8")

    print(f"見本: {SOURCE_DIR / SOURCE_FILES[args.id]} → {TEXTURE_SIZE}x{TEXTURE_SIZE} へエリア平均（白背景は段階透過）")
    for path in (asset_model, texture, list_model):
        print(f"生成: {path.relative_to(ROOT)}  ({path.stat().st_size} bytes)")
    for kind in IMAGE_KINDS:
        path = ITEM_LIST / "images" / f"{args.id}{kind}.svg"
        print(f"生成: {path.relative_to(ROOT)}  ({path.stat().st_size} bytes)")
    print("      3 枚の画像はすべて同じ 3D モデル JSON と実テクスチャから組み立てています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
