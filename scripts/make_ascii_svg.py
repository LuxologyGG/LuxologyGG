"""
Step 3b — Convert the prepped grayscale image into a self-typing ASCII SVG.

Downsamples to a character grid, maps brightness -> glyph on a density ramp,
and wraps each row in a horizontal clip-path wipe (staggered top to bottom)
so the portrait "types" itself in once, then freezes. Monochrome, high
contrast — no per-character color, no looping.

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [avi-ascii.svg]
"""
import sys
from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space clears bg
COLS = 100
ROWS = 53
CHAR_W = 6.0
CHAR_H = 11.0
FONT_SIZE = 11
FILL = "#8b949e"  # light-gray, monochrome
FONT = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"


def brightness_to_glyph(v: int) -> str:
    idx = int((255 - v) / 255 * (len(RAMP) - 1))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def build_grid(img_path: str, cols: int, rows: int):
    im = Image.open(img_path).convert("L").resize((cols, rows))
    px = im.load()
    grid = []
    for y in range(rows):
        row = "".join(brightness_to_glyph(px[x, y]) for x in range(cols))
        grid.append(row)
    return grid


def escape(c: str) -> str:
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(c, c)


def make_svg(grid, out_path: str):
    width = COLS * CHAR_W
    height = ROWS * CHAR_H
    total_rows = len(grid)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}">'
    )
    parts.append(f"<rect width='100%' height='100%' fill='none'/>")
    parts.append(
        f"<style>text {{ font-family: {FONT}; font-size: {FONT_SIZE}px; fill: {FILL}; "
        f"white-space: pre; }}</style>"
    )
    parts.append("<defs>")

    stagger = 0.045  # seconds between row starts
    row_dur = 0.5    # seconds for a row to wipe in

    for i, row in enumerate(grid):
        clip_id = f"clip{i}"
        start = i * stagger
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="0" y="{i*CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{width:.0f}" '
            f'begin="{start:.3f}s" dur="{row_dur}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.4 0 0.2 1"/>'
            f"</rect>"
            f"</clipPath>"
        )
    parts.append("</defs>")

    for i, row in enumerate(grid):
        clip_id = f"clip{i}"
        text = escape(row).replace(" ", " ")
        y = i * CHAR_H + FONT_SIZE
        parts.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{y:.1f}" xml:space="preserve">{text}</text>'
            f"</g>"
        )

    parts.append("</svg>")
    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "../avi-ascii.svg"
    grid = build_grid(src, COLS, ROWS)
    make_svg(grid, out)
