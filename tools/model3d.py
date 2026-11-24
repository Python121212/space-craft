#!/usr/bin/env python3
"""Minecraft のモデル JSON（elements）から **3D の SVG** を組み立てる共通モジュール。

標準ライブラリのみ。`tools/catalog.py`（一覧全般）と `tools/itemart.py`（アイテム）の
両方から使います。ビルドには一切組み込みません。

対応しているもの:
    elements[].from / to           … 直方体の頂点
    elements[].faces.<面>.uv       … テクスチャ PNG のどの色で面を塗るか
    elements[].faces.<面>.texture  … "#0" などのテクスチャ参照（色は uv で決まります）
    視点 yaw / pitch               … カメラ方向から自動で背面をカリングし、奥から手前へ描画

まだ対応していないもの（必要になったら拡張してください）:
    elements[].rotation、parent の継承、面ごとのテクスチャ補間
    （1 面は uv の中心色で塗ります。`画像/` の見本を 16x16 に落とした実テクスチャを想定）
"""

from __future__ import annotations

import html
import json
import math
import struct
import zlib
from pathlib import Path

# 面 -> (外向き法線, 頂点を作る関数)
DEFAULT_FACE_COLORS = {
    "up": "#c3ced9",
    "down": "#4b5666",
    "north": "#7d8896",
    "south": "#626d7c",
    "west": "#8c98a6",
    "east": "#8592a1",
}


def element_faces(el: dict) -> list[tuple[str, tuple[int, int, int], list[tuple[float, float, float]]]]:
    """1 つの element から 6 面を取り出す。Minecraft 座標は x=右, y=上, z=奥, 0..16。"""
    x0, y0, z0 = el["from"]
    x1, y1, z1 = el["to"]
    return [
        ("up",    (0, 1, 0),  [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]),
        ("down",  (0, -1, 0), [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)]),
        ("north", (0, 0, -1), [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)]),
        ("south", (0, 0, 1),  [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]),
        ("west",  (-1, 0, 0), [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)]),
        ("east",  (1, 0, 0),  [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)]),
    ]


class Palette:
    """テクスチャ PNG を RGBA に正規化して保持し、uv の中心色を取り出すリーダー。

    `rows[y][x]` は常に (r, g, b, a)。Minecraft の uv は 0..16 で指定されるため、
    画像の実サイズが 256x256 でも同じ座標が対応するブロックを指します。
    """

    def __init__(self, width: int, height: int, rows: list[list[tuple[int, int, int, int]]]):
        self.width, self.height, self.rows = width, height, rows

    def pixel(self, x: int, y: int) -> tuple[int, int, int, int]:
        return self.rows[max(0, min(self.height - 1, y))][max(0, min(self.width - 1, x))]

    def sample(self, uv: list[float] | None) -> str | None:
        if not uv or len(uv) != 4:
            return None
        # Minecraft の uv は 0..16 のテクスチャ座標。実画像サイズへ比例させる。
        u = (uv[0] + uv[2]) / 2 / 16 * self.width
        v = (uv[1] + uv[3]) / 2 / 16 * self.height
        r, g, b, a = self.pixel(int(u), int(v))
        if a < 128:  # 透明なら既定色に任せる
            return None
        return f"#{r:02x}{g:02x}{b:02x}"

    def pixel_at_uv(self, x: float, y: float) -> tuple[int, int, int, int]:
        """0..16 の uv 座標から 1 ピクセルを取得（16x16 へのダウンサンプル用）。"""
        return self.pixel(int(x / 16 * self.width), int(y / 16 * self.height))


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else (b if pb <= pc else c)


def read_png(path: Path) -> Palette | None:
    """PNG を標準ライブラリだけで RGBA に復号する。

    対応: color type 0 / 2 / 3 / 4 / 6（gray / RGB / パレット / gray+α / RGBA）、
    全 filter（None / Sub / Up / Average / Paeth）、tRNS、8bit。
    非対応: インターレース、16bit（ユーザーが `画像/` に置く普通の PNG はほぼ 8bit です）。
    """
    path = Path(path)
    if not path.is_file():
        return None
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    off, idat = 8, bytearray()
    width = height = depth = ctype = interlace = None
    plte: bytes | None = None
    trns: bytes | None = None
    while off + 8 <= len(data):
        size = struct.unpack_from(">I", data, off)[0]
        tag = data[off + 4:off + 8]
        chunk = data[off + 8:off + 8 + size]
        off += 12 + size
        if tag == b"IHDR":
            width, height, depth, ctype, _comp, _filt, interlace = struct.unpack_from(">IIBBBBB", chunk)
        elif tag == b"PLTE":
            plte = chunk
        elif tag == b"tRNS":
            trns = chunk
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
    if not (width and height and depth == 8 and ctype in (0, 2, 3, 4, 6) and interlace == 0):
        return None
    if ctype == 3 and not plte:
        return None
    bpp = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(bytes(idat))
    stride = width * bpp
    decoded: list[bytes] = []
    pos = 0
    for _ in range(height):
        filt = raw[pos]
        pos += 1
        line = bytearray(raw[pos:pos + stride])
        pos += stride
        if filt:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = decoded[-1][i] if decoded else 0
                c = decoded[-1][i - bpp] if decoded and i >= bpp else 0
                if filt == 1:
                    line[i] = (line[i] + a) & 0xFF
                elif filt == 2:
                    line[i] = (line[i] + b) & 0xFF
                elif filt == 3:
                    line[i] = (line[i] + (a + b) // 2) & 0xFF
                elif filt == 4:
                    line[i] = (line[i] + _paeth(a, b, c)) & 0xFF
                else:
                    raise ValueError(f"不明な PNG filter {filt}: {path}")
        decoded.append(bytes(line))

    rows: list[list[tuple[int, int, int, int]]] = []
    for y in range(height):
        line = decoded[y]
        row: list[tuple[int, int, int, int]] = []
        for x in range(width):
            px = line[x * bpp:(x + 1) * bpp]
            if ctype == 2:
                row.append((px[0], px[1], px[2], 255))
            elif ctype == 6:
                row.append((px[0], px[1], px[2], px[3]))
            elif ctype == 0:
                row.append((px[0], px[0], px[0], 255))
            elif ctype == 4:
                row.append((px[0], px[0], px[0], px[1]))
            else:  # ctype == 3（インデックスカラー）
                i = px[0]
                r, g, b = plte[i * 3:i * 3 + 3]
                a = trns[i] if trns and i < len(trns) else 255
                row.append((r, g, b, a))
        rows.append(row)
    return Palette(width, height, rows)


# 旧名も残す（catalog.py などからの互換用）
read_palette = read_png


def camera_basis(yaw: float, pitch: float):
    """カメラ方向 c と、画面の右 r / 上 u の単位ベクトルを返す。"""
    a, b = math.radians(yaw), math.radians(pitch)
    c = (math.cos(b) * math.cos(a), math.sin(b), math.cos(b) * math.sin(a))
    rx, rz = c[2], -c[0]  # cross((0,1,0), c)
    n = math.hypot(rx, rz) or 1.0
    r = (rx / n, 0.0, rz / n)
    u = (
        c[1] * r[2] - c[2] * r[1],
        c[2] * r[0] - c[0] * r[2],
        c[0] * r[1] - c[1] * r[0],
    )  # cross(c, r)
    return c, r, u


def project(p, r, u, c, center, scale) -> tuple[float, float, float]:
    """3D 点 -> (画面 x, 画面 y, 奥行き)。画面 y は下向き。"""
    dx, dy, dz = p[0] - center[0], p[1] - center[1], p[2] - center[2]
    sx = (dx * r[0] + dy * r[1] + dz * r[2]) * scale
    sy = -(dx * u[0] + dy * u[1] + dz * u[2]) * scale
    depth = dx * c[0] + dy * c[1] + dz * c[2]
    return sx, sy, depth


def scene(
    model_path: Path,
    *,
    yaw: float = 45.0,
    pitch: float = 32.0,
    scale: float = 12.0,
    palette_path: Path | None = None,
):
    """モデル JSON を読み、可視面だけを奥から手前へ並べた polygon 群を返す。

    戻り値: ([(depth, color, [(x, y), ...]), ...], note)
    """
    data = json.loads(Path(model_path).read_text(encoding="utf-8"))
    elements = data.get("elements")
    note = ""
    if not elements:
        elements = [{"from": [0, 0, 0], "to": [16, 16, 16], "faces": {}}]
        note = "（elements が無いため既定の立方体を描画しました）"

    palette = read_palette(palette_path) if palette_path else None
    c, r, u = camera_basis(yaw, pitch)
    center = (8.0, 8.0, 8.0)
    polygons: list[tuple[float, str, list[tuple[float, float]]]] = []

    for el in elements:
        faces = el.get("faces", {})
        for name, normal, points in element_faces(el):
            if sum(normal[i] * c[i] for i in range(3)) <= 1e-6:
                continue  # 裏面は描かない
            face = faces.get(name, {})
            color = palette.sample(face.get("uv")) if palette else None
            color = color or DEFAULT_FACE_COLORS[name]
            projected = [project(p, r, u, c, center, scale) for p in points]
            depth = sum(pr[2] for pr in projected) / len(projected)
            polygons.append((depth, color, [(pr[0], pr[1]) for pr in projected]))

    polygons.sort(key=lambda item: item[0])
    return polygons, note


def bounds(polygons) -> tuple[float, float, float, float]:
    pts = [p for _, _, poly in polygons for p in poly]
    if not pts:
        return 0.0, 0.0, 1.0, 1.0
    return (
        min(p[0] for p in pts), min(p[1] for p in pts),
        max(p[0] for p in pts), max(p[1] for p in pts),
    )


def place(polygons, ox: float, oy: float, stroke: str = "#2b3038", width: float = 1.2) -> list[str]:
    """polygon 群を translate して <g> に包んだ SVG 行を返す。"""
    lines = [f'  <g transform="translate({ox:.2f},{oy:.2f})">']
    for _, color, poly in polygons:
        coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in poly)
        lines.append(
            f'    <polygon points="{coords}" fill="{color}" stroke="{stroke}" stroke-width="{width}"/>'
        )
    lines.append("  </g>")
    return lines


def document(
    canvas_w: int,
    canvas_h: int,
    body: list[str],
    label: str,
    *,
    background: list[str] | None = None,
    bg_color: str = "#15181e",
    label_y: int | None = None,
) -> str:
    """背景・本文・ラベルを 1 枚の独立した SVG にまとめる。"""
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'viewBox="0 0 {canvas_w} {canvas_h}" role="img" aria-label="{html.escape(label)}">',
        f'  <rect width="100%" height="100%" fill="{bg_color}" rx="8"/>',
    ]
    if background:
        lines += ["  " + line for line in background]
    lines += body
    lines.append(
        f'  <text x="{canvas_w / 2:.0f}" y="{label_y or canvas_h - 20}" fill="#8b949e" '
        f'font-family="sans-serif" font-size="11" text-anchor="middle">{html.escape(label)}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def standalone_svg(
    model_path: Path,
    title: str,
    *,
    palette_path: Path | None = None,
    scale: float = 13.0,
    yaw: float = 45.0,
    pitch: float = 32.0,
) -> tuple[str, str]:
    """単体の 3D 全体図を 1 枚の SVG 文字列として作る。戻り値は (SVG, 補足)。"""
    polygons, note = scene(model_path, yaw=yaw, pitch=pitch, scale=scale, palette_path=palette_path)
    minx, miny, maxx, maxy = bounds(polygons)
    pad_x, pad_top, pad_bottom = 44, 40, 56
    w = int(maxx - minx + pad_x * 2)
    h = int(maxy - miny + pad_top + pad_bottom)
    body = place(polygons, -minx + pad_x, -miny + pad_top)
    return document(w, h, body, title), note
