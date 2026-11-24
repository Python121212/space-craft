#!/usr/bin/env python3
"""アイテムのテクスチャと、一覧 md 用の画像を生成する（標準ライブラリのみ・外部依存なし）。

    python3 tools/itemart.py wrench

生成物:
    src/main/resources/assets/spacecraft/textures/item/<id>.png  … 16x16 の実テクスチャ
    アイテム一覧/images/<id>_inventory.svg … インベントリ内の状態
    アイテム一覧/images/<id>_held.svg      … 手に持った状態

画像はすべて**同じ実テクスチャから組み立てた模式図**です。ゲーム内スクリーンショットが
撮れるようになったら同名の PNG を置き、md の画像リンクと表の拡張子を .svg → .png に
書き換えてください（catalog.py はどちらの拡張子も受理します）。

SVG は PNG を data URI で埋め込まず、16x16 のピクセルを <rect> に展開します。
GitHub の md サニタイズでも消えず、そのまま表示できます。
"""

from __future__ import annotations

import argparse
import html
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ITEM_LIST = ROOT / "アイテム一覧"
TEXTURE_DIR = ROOT / "src/main/resources/assets/spacecraft/textures/item"
ID_RE = re.compile(r"^[a-z0-9_]+$")

# RGBA
TRANSPARENT = (0, 0, 0, 0)
OUTLINE = (38, 44, 54, 255)
METAL = (150, 163, 178, 255)
LIGHT = (214, 223, 233, 255)
GRIP = (56, 68, 82, 255)
CYAN = (79, 209, 197, 255)  # 宇宙クラフトのアクセント


def wrench_texture() -> list[list[tuple[int, int, int, int]]]:
    """16x16 のレンチ（左に開口・中央に柄・右にグリップ）。"""
    px = [[TRANSPARENT for _ in range(16)] for _ in range(16)]

    def fill(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < 16 and 0 <= y < 16:
                    px[y][x] = color

    # 右端のグリップ
    fill(11, 6, 15, 9, GRIP)
    fill(11, 6, 15, 6, OUTLINE)
    fill(15, 7, 15, 8, OUTLINE)
    fill(12, 7, 13, 8, CYAN)

    # 中央の柄
    fill(4, 7, 11, 8, METAL)
    fill(4, 7, 11, 7, LIGHT)
    fill(4, 6, 11, 6, OUTLINE)
    fill(4, 9, 11, 9, OUTLINE)

    # 左端の開口（C 字）
    fill(1, 4, 4, 4, OUTLINE)
    fill(1, 5, 4, 5, METAL)
    fill(0, 5, 0, 10, OUTLINE)
    fill(1, 6, 1, 9, METAL)
    fill(1, 10, 4, 10, METAL)
    fill(1, 11, 4, 11, OUTLINE)
    fill(2, 6, 3, 9, TRANSPARENT)  # U 字の穴
    return px


def texture_for(id_: str) -> list[list[tuple[int, int, int, int]]]:
    if id_ == "wrench":
        return wrench_texture()
    raise ValueError(f"テクスチャ定義がありません: {id_}（tools/itemart.py に追加してください）")


def png_bytes(px: list[list[tuple[int, int, int, int]]]) -> bytes:
    """RGBA PNG を標準ライブラリだけで書き出す。"""
    height, width = len(px), len(px[0])
    raw = bytearray()
    for row in px:
        raw.append(0)  # filter: None
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


def pixel_rects(px: list[list[tuple[int, int, int, int]]], scale: int, ox: int, oy: int) -> list[str]:
    """16x16 の各ピクセルを <rect> に展開（data URI を使わない）。"""
    lines = [f'  <g transform="translate({ox},{oy}) scale({scale})" shape-rendering="crispEdges">']
    for y, row in enumerate(px):
        for x, (r, g, b, a) in enumerate(row):
            if a:
                lines.append(f'    <rect x="{x}" y="{y}" width="1" height="1" fill="#{r:02x}{g:02x}{b:02x}"/>')
    lines.append("  </g>")
    return lines


def inventory_svg(px, id_: str) -> str:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="224" '
        'viewBox="0 0 200 224" role="img" '
        f'aria-label="{html.escape(id_)} のインベントリ内の状態">',
        '  <rect width="100%" height="100%" fill="#1b1e24" rx="8"/>',
        '  <rect x="36" y="30" width="128" height="128" fill="#8b8b8b" stroke="#373737" stroke-width="4"/>',
        '  <path d="M40 34 L160 34 L40 154 Z" fill="#ffffff" opacity="0.12"/>',
        '  <path d="M160 34 L160 154 L40 154 Z" fill="#000000" opacity="0.18"/>',
    ]
    lines += pixel_rects(px, 6, 52, 46)
    lines += [
        f'  <text x="100" y="190" fill="#e6edf3" font-family="sans-serif" font-size="14" '
        f'text-anchor="middle">spacecraft:{html.escape(id_)}</text>',
        '  <text x="100" y="210" fill="#8b949e" font-family="sans-serif" font-size="11" '
        'text-anchor="middle">インベントリ内の状態（実テクスチャから生成）</text>',
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def held_svg(px, id_: str) -> str:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240" '
        'viewBox="0 0 320 240" role="img" '
        f'aria-label="{html.escape(id_)} を手に持った状態">',
        '  <rect width="100%" height="100%" fill="#101820" rx="8"/>',
    ]
    # 宇宙っぽい背景の星
    for x, y, r in ((36, 32, 1.6), (82, 58, 1.1), (268, 44, 1.8), (298, 96, 1.2), (52, 120, 1.0)):
        lines.append(f'  <circle cx="{x}" cy="{y}" r="{r}" fill="#4fd1c5" opacity="0.55"/>')
    # 簡易的な腕・手
    lines += [
        '  <path d="M214 240 L232 156 L286 168 L306 240 Z" fill="#b9805c"/>',
        '  <path d="M232 156 L286 168 L280 186 L228 174 Z" fill="#d69a72"/>',
    ]
    # レンチを斜めに構える
    lines.append('  <g transform="translate(126,74) rotate(-34 48 48)">')
    lines += pixel_rects(px, 5, 0, 0)
    lines.append("  </g>")
    lines += [
        f'  <text x="160" y="34" fill="#e6edf3" font-family="sans-serif" font-size="14" '
        f'text-anchor="middle">spacecraft:{html.escape(id_)}</text>',
        '  <text x="160" y="224" fill="#8b949e" font-family="sans-serif" font-size="11" '
        'text-anchor="middle">手に持った状態（実テクスチャから生成）</text>',
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id", help="アイテム id（現在は wrench のみ）")
    args = ap.parse_args()

    if not ID_RE.match(args.id):
        print("エラー: id は半角英小文字・数字・アンダースコアのみ", file=sys.stderr)
        return 1
    try:
        px = texture_for(args.id)
    except ValueError as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1

    png = png_bytes(px)
    texture = TEXTURE_DIR / f"{args.id}.png"
    inventory = ITEM_LIST / "images" / f"{args.id}_inventory.svg"
    held = ITEM_LIST / "images" / f"{args.id}_held.svg"
    for path in (texture, inventory, held):
        path.parent.mkdir(parents=True, exist_ok=True)

    texture.write_bytes(png)
    inventory.write_text(inventory_svg(px, args.id), encoding="utf-8")
    held.write_text(held_svg(px, args.id), encoding="utf-8")

    for path in (texture, inventory, held):
        print(f"生成: {path.relative_to(ROOT)}  ({path.stat().st_size} bytes)")
    print("      3 点はすべて同じ 16x16 テクスチャから組み立てています。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
