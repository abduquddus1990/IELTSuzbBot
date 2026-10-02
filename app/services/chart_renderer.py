"""Render Writing Task 1 visuals (bar, line, pie, table, process, map) to PNG with Pillow.

Kept dependency-free (no matplotlib) so it runs on the free Render instance. Output is cached
per test id because the data never changes at runtime.
"""

from __future__ import annotations

import io
import math
from functools import lru_cache
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from app.services.content.writing_charts import TASK1_CHARTS

PALETTE = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#0891b2"]
INK = "#1f2937"
MUTED = "#6b7280"
GRID = "#e5e7eb"
WIDTH, HEIGHT = 1200, 720


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in (("DejaVuSans-Bold.ttf", "arialbd.ttf") if bold else ("DejaVuSans.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _text_w(draw: ImageDraw.ImageDraw, text: str, font: Any) -> float:
    return draw.textlength(text, font=font)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: Any, max_w: float) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if _text_w(draw, trial, font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _nice_max(value: float) -> float:
    if value <= 0:
        return 1.0
    exp = 10 ** math.floor(math.log10(value))
    for step in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if step * exp >= value:
            return step * exp
    return 10 * exp


def _legend(draw: ImageDraw.ImageDraw, names: list[str], x: float, y: float) -> None:
    font = _font(18)
    for i, name in enumerate(names):
        draw.rectangle([x, y + 4, x + 18, y + 22], fill=PALETTE[i % len(PALETTE)])
        draw.text((x + 26, y), name, fill=INK, font=font)
        x += 26 + _text_w(draw, name, font) + 28


def _axes(draw, box, y_max, y_label, ticks=5):
    x0, y0, x1, y1 = box
    font = _font(16)
    for i in range(ticks + 1):
        val = y_max * i / ticks
        yy = y1 - (y1 - y0) * i / ticks
        draw.line([x0, yy, x1, yy], fill=GRID, width=1)
        label = f"{val:g}"
        draw.text((x0 - 10 - _text_w(draw, label, font), yy - 9), label, fill=MUTED, font=font)
    draw.line([x0, y0, x0, y1], fill=INK, width=2)
    draw.line([x0, y1, x1, y1], fill=INK, width=2)
    if y_label:
        draw.text((x0, y0 - 28), y_label, fill=MUTED, font=font)


def _draw_bar(draw, spec, box):
    x0, y0, x1, y1 = box
    series = spec["series"]
    cats = spec["categories"]
    y_max = _nice_max(max(max(s["values"]) for s in series) * 1.08)
    _axes(draw, box, y_max, spec.get("y_label", ""))
    slot = (x1 - x0) / len(cats)
    bar_w = slot * 0.7 / len(series)
    font, small = _font(17), _font(14)
    for ci, cat in enumerate(cats):
        sx = x0 + slot * ci + slot * 0.15
        for si, s in enumerate(series):
            v = s["values"][ci]
            top = y1 - (y1 - y0) * v / y_max
            bx = sx + bar_w * si
            draw.rectangle([bx, top, bx + bar_w - 3, y1 - 1], fill=PALETTE[si % len(PALETTE)])
            label = f"{v:g}"
            draw.text((bx + (bar_w - 3) / 2 - _text_w(draw, label, small) / 2, top - 18), label, fill=INK, font=small)
        cx = x0 + slot * ci + slot / 2
        draw.text((cx - _text_w(draw, cat, font) / 2, y1 + 8), cat, fill=INK, font=font)
    if len(series) > 1 or series[0].get("name"):
        _legend(draw, [s["name"] for s in series], x0, y1 + 40)


def _draw_line(draw, spec, box):
    x0, y0, x1, y1 = box
    series, xs = spec["series"], spec["x"]
    y_max = _nice_max(max(max(s["values"]) for s in series) * 1.08)
    _axes(draw, box, y_max, spec.get("y_label", ""))
    step = (x1 - x0 - 40) / max(1, len(xs) - 1)
    font = _font(16)
    for i, x in enumerate(xs):
        px = x0 + 20 + step * i
        draw.text((px - _text_w(draw, x, font) / 2, y1 + 8), x, fill=INK, font=font)
    for si, s in enumerate(series):
        color = PALETTE[si % len(PALETTE)]
        pts = [(x0 + 20 + step * i, y1 - (y1 - y0) * v / y_max) for i, v in enumerate(s["values"])]
        draw.line(pts, fill=color, width=4, joint="curve")
        for px, py in pts:
            draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=color)
    _legend(draw, [s["name"] for s in series], x0, y1 + 40)


def _draw_pie(draw, spec, box):
    x0, y0, x1, y1 = box
    pies = spec["pies"]
    labels = [sl["label"] for sl in pies[0]["slices"]]
    color_of = {label: PALETTE[i % len(PALETTE)] for i, label in enumerate(labels)}
    w = (x1 - x0) / len(pies)
    r = min(w * 0.36, (y1 - y0) * 0.38)
    title_f, small = _font(22, bold=True), _font(17, bold=True)
    for pi, pie in enumerate(pies):
        cx, cy = x0 + w * pi + w / 2, y0 + (y1 - y0) / 2 + 10
        draw.text((cx - _text_w(draw, pie["title"], title_f) / 2, y0 - 10), pie["title"], fill=INK, font=title_f)
        total = sum(sl["value"] for sl in pie["slices"])
        start = -90.0
        for sl in pie["slices"]:
            extent = 360.0 * sl["value"] / total
            draw.pieslice([cx - r, cy - r, cx + r, cy + r], start, start + extent, fill=color_of[sl["label"]], outline="white", width=2)
            mid = math.radians(start + extent / 2)
            label = f"{sl['value']}%"
            lx, ly = cx + math.cos(mid) * (r + 28), cy + math.sin(mid) * (r + 28)
            draw.text((lx - _text_w(draw, label, small) / 2, ly - 10), label, fill=INK, font=small)
            start += extent
    _legend(draw, labels, x0, y1 + 20)


def _draw_table(draw, spec, box):
    x0, y0, x1, _ = box
    cols, rows = spec["columns"], spec["rows"]
    head_f, cell_f = _font(19, bold=True), _font(20)
    col_w = (x1 - x0) / len(cols)
    head_lines = [_wrap(draw, c, head_f, col_w - 20) for c in cols]
    head_h = 24 * max(len(h) for h in head_lines) + 20
    draw.rectangle([x0, y0, x1, y0 + head_h], fill="#dbeafe", outline=INK)
    for ci, lines in enumerate(head_lines):
        for li, line in enumerate(lines):
            draw.text((x0 + col_w * ci + 10, y0 + 10 + 24 * li), line, fill=INK, font=head_f)
    row_h = 52
    for ri, row in enumerate(rows):
        top = y0 + head_h + row_h * ri
        draw.rectangle([x0, top, x1, top + row_h], fill="#ffffff" if ri % 2 == 0 else "#f8fafc", outline="#cbd5e1")
        for ci, cell in enumerate(row):
            draw.text((x0 + col_w * ci + 10, top + 14), cell, fill=INK, font=cell_f)
    for ci in range(1, len(cols)):
        xx = x0 + col_w * ci
        draw.line([xx, y0, xx, y0 + head_h + row_h * len(rows)], fill="#cbd5e1")


def _draw_process(draw, spec, box):
    x0, y0, x1, y1 = box
    steps = spec["steps"]
    per_row = math.ceil(len(steps) / 2)
    gap_x = 36
    bw = (x1 - x0 - gap_x * (per_row - 1)) / per_row
    bh = 130
    font, num_f = _font(17), _font(18, bold=True)
    positions = []
    for i in range(len(steps)):
        row = i // per_row
        col = i % per_row if row == 0 else per_row - 1 - (i % per_row)  # snake layout
        bx = x0 + col * (bw + gap_x)
        by = y0 + 20 + row * (bh + 90)
        positions.append((bx, by))
    for i, step in enumerate(steps):
        bx, by = positions[i]
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill="#eff6ff", outline="#2563eb", width=2)
        draw.text((bx + 12, by + 8), str(i + 1), fill="#2563eb", font=num_f)
        for li, line in enumerate(_wrap(draw, step, font, bw - 24)[:5]):
            draw.text((bx + 12, by + 34 + 20 * li), line, fill=INK, font=font)
        if i + 1 < len(steps):
            nx, ny = positions[i + 1]
            if ny == by:
                ax0, ax1 = (bx + bw, nx) if nx > bx else (bx, nx + bw)
                ay = by + bh / 2
                draw.line([ax0 + 4, ay, ax1 - 4, ay], fill=INK, width=3)
                tip = ax1 - 4 if nx > bx else ax1 + 4
                d = -12 if nx > bx else 12
                draw.polygon([(tip, ay), (tip + d, ay - 8), (tip + d, ay + 8)], fill=INK)
            else:
                ax = bx + bw / 2
                draw.line([ax, by + bh + 4, ax, ny - 6], fill=INK, width=3)
                draw.polygon([(ax, ny - 4), (ax - 8, ny - 16), (ax + 8, ny - 16)], fill=INK)
    # arrow back to start to show the cycle
    (lx, ly), (fx, fy) = positions[-1], positions[0]
    draw.line([lx, ly + bh / 2, x0 - 14, ly + bh / 2, x0 - 14, fy + bh / 2, fx - 4, fy + bh / 2], fill=MUTED, width=2)
    draw.polygon([(fx - 2, fy + bh / 2), (fx - 14, fy + bh / 2 - 7), (fx - 14, fy + bh / 2 + 7)], fill=MUTED)


def _draw_map(draw, spec, box):
    x0, y0, x1, y1 = box
    maps = spec["maps"]
    w = (x1 - x0) / len(maps)
    fills = {"building": "#e0e7ff", "open": "#ecfccb", "road": "#d1d5db", "trees": "#86efac"}
    title_f, font = _font(22, bold=True), _font(16)
    for mi, m in enumerate(maps):
        mx0, my0 = x0 + w * mi + 15, y0 + 30
        mw, mh = w - 30, y1 - y0 - 40
        draw.text((mx0 + mw / 2 - _text_w(draw, m["title"], title_f) / 2, y0 - 6), m["title"], fill=INK, font=title_f)
        draw.rectangle([mx0, my0, mx0 + mw, my0 + mh], outline=INK, width=2, fill="#ffffff")
        for it in m["items"]:
            ix0, iy0 = mx0 + mw * it["x"] / 100, my0 + mh * it["y"] / 100
            ix1, iy1 = ix0 + mw * it["w"] / 100, iy0 + mh * it["h"] / 100
            draw.rectangle([ix0, iy0, ix1, iy1], fill=fills.get(it.get("kind", "building"), "#e5e7eb"), outline="#475569")
            lines = _wrap(draw, it["label"], font, ix1 - ix0 - 8)
            ty = (iy0 + iy1) / 2 - 10 * len(lines)
            for line in lines:
                draw.text(((ix0 + ix1) / 2 - _text_w(draw, line, font) / 2, ty), line, fill=INK, font=font)
                ty += 20
        draw.text((mx0 + mw - 22, my0 + 6), "N", fill=INK, font=_font(18, bold=True))


_DRAWERS = {"bar": _draw_bar, "line": _draw_line, "pie": _draw_pie, "table": _draw_table, "process": _draw_process, "map": _draw_map}
_INNER_BOX = {"bar": (90, 60, -30, -110), "line": (90, 60, -30, -110), "pie": (20, 40, -20, -70), "table": (30, 20, -30, -20), "process": (40, 10, -20, -20), "map": (0, 20, 0, -10)}


def _draw_spec(draw: ImageDraw.ImageDraw, spec: dict[str, Any], area: tuple[float, float, float, float], show_title: bool) -> None:
    ax0, ay0, ax1, ay1 = area
    if show_title and spec.get("title"):
        f = _font(24, bold=True)
        for li, line in enumerate(_wrap(draw, spec["title"], f, ax1 - ax0 - 20)):
            draw.text(((ax0 + ax1) / 2 - _text_w(draw, line, f) / 2, ay0 + 8 + 30 * li), line, fill=INK, font=f)
        ay0 += 50
    if spec["type"] == "panels":
        n = len(spec["panels"])
        pw = (ax1 - ax0) / n
        for i, panel in enumerate(spec["panels"]):
            _draw_spec(draw, panel, (ax0 + pw * i, ay0, ax0 + pw * (i + 1), ay1), show_title=True)
        return
    l, t, r, b = _INNER_BOX[spec["type"]]
    _DRAWERS[spec["type"]](draw, spec, (ax0 + l, ay0 + t, ax1 + r, ay1 + b))


def render_chart_png(spec: dict[str, Any]) -> bytes:
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    draw = ImageDraw.Draw(img)
    _draw_spec(draw, spec, (0, 0, WIDTH, HEIGHT), show_title=True)
    # Trim unused white space (tables and process diagrams are shorter than the canvas).
    bbox = Image.eval(img.convert("L"), lambda p: 255 - p).getbbox()
    if bbox:
        img = img.crop((0, 0, WIDTH, min(HEIGHT, bbox[3] + 24)))
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@lru_cache(maxsize=32)
def render_task1_chart(test_id: str) -> bytes | None:
    spec = TASK1_CHARTS.get(test_id)
    return render_chart_png(spec) if spec else None
