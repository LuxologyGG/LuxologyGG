"""
Step 4 — Build the neofetch-style info card SVG.

Hand-authored: a title bar, then colored key/value rows (Now, Prev, Stack,
Highlights). Each line fades + slides in on a short stagger. Set STATIC=1
to emit a frozen frame (no animation) for local Quick Look previews.

Edit CONFIG below to update your own info -- this is the "story numbers
can't tell" card; the heatmap already covers raw GitHub stats.

Usage:
    python scripts/make_info_card.py            # animated
    STATIC=1 python scripts/make_info_card.py    # frozen frame
"""
import os
import sys

CONFIG = {
    "user": "luxologygg",
    "now": "Founder",
    "prev": "Full-Stack Engineer",
    "stack": "HTML5 · CSS3 · JS · React · Figma · WordPress · Python · R · "
             "PHP · Node · Git · GitHub · npm · Vercel · Cloudflare · "
             "VS Code · Homebrew",
    "highlights": [
        "Contributor — badges/shields (shields.io)",
        "Contributor — facebook/react",
    ],
}

WIDTH = 490
LINE_H = 24
PAD_X = 18
TITLE_H = 34
FONT = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"

BG = "#0d1117"
BORDER = "#30363d"
TITLE_BG = "#161b22"
LABEL_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
DIM = "#8b949e"
DOT_RED = "#ff5f56"
DOT_YEL = "#ffbd2e"
DOT_GRN = "#27c93f"


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def wrap(text: str, max_chars: int):
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if len(trial) > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def build_rows(cfg):
    rows = []
    rows.append(("Now", cfg["now"]))
    rows.append(("Prev", cfg["prev"]))
    for line in wrap(cfg["stack"], 46):
        rows.append(("Stack" if line == wrap(cfg["stack"], 46)[0] else "", line))
    for i, h in enumerate(cfg["highlights"]):
        rows.append(("Highlights" if i == 0 else "", h))
    return rows


def make_svg(cfg, out_path, static=False):
    rows = build_rows(cfg)
    height = TITLE_H + len(rows) * LINE_H + 16

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}">'
    )
    parts.append(
        f"<style>"
        f".mono {{ font-family: {FONT}; font-size: 13px; }}"
        f".label {{ fill: {LABEL_COLOR}; font-weight: 600; }}"
        f".value {{ fill: {VALUE_COLOR}; }}"
        f".dim {{ fill: {DIM}; }}"
        f"</style>"
    )

    # window chrome
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{height}" rx="8" '
                  f'fill="{BG}" stroke="{BORDER}" stroke-width="1"/>')
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{TITLE_H}" rx="8" fill="{TITLE_BG}"/>')
    parts.append(f'<rect x="0" y="{TITLE_H-8}" width="{WIDTH}" height="8" fill="{TITLE_BG}"/>')
    parts.append(f'<circle cx="18" cy="{TITLE_H/2:.0f}" r="6" fill="{DOT_RED}"/>')
    parts.append(f'<circle cx="38" cy="{TITLE_H/2:.0f}" r="6" fill="{DOT_YEL}"/>')
    parts.append(f'<circle cx="58" cy="{TITLE_H/2:.0f}" r="6" fill="{DOT_GRN}"/>')
    parts.append(
        f'<text x="{WIDTH/2:.0f}" y="{TITLE_H/2+4:.0f}" text-anchor="middle" '
        f'class="mono dim">neofetch — {esc(cfg["user"])}@github</text>'
    )

    y = TITLE_H + 22
    stagger = 0.09
    for i, (label, value) in enumerate(rows):
        row_y = y + i * LINE_H
        label_x = PAD_X
        value_x = PAD_X + 92
        anim = ""
        group_start = ""
        group_end = "</g>"
        if not static:
            begin = i * stagger
            anim = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="0.25s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-8 0" to="0 0" begin="{begin:.2f}s" dur="0.25s" '
                f'fill="freeze" calcMode="spline" keySplines="0.4 0 0.2 1"/>'
            )
            group_start = f'<g opacity="0">'
        else:
            group_start = "<g>"

        parts.append(group_start)
        if anim:
            parts.append(anim)
        if label:
            parts.append(
                f'<text x="{label_x}" y="{row_y}" class="mono label">{esc(label)}</text>'
            )
        parts.append(
            f'<text x="{value_x}" y="{row_y}" class="mono value">{esc(value)}</text>'
        )
        parts.append(group_end)

    parts.append("</svg>")
    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "../info-card.svg"
    static = bool(os.environ.get("STATIC"))
    make_svg(CONFIG, out, static=static)
