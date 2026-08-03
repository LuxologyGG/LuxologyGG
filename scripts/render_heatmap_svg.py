"""
Step 5b — Draw the 53-week x 7-day contribution grid as an animated SVG.

Reads data/contributions.json (written by fetch_contributions.py) and
renders rounded, colored boxes on a GitHub-ish green ramp. Reveals once
with a diagonal, line-after-line slide-down (plays on load, then freezes --
no looping "glow"). Adds a Less->More legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py
"""
import json
from datetime import datetime, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BOX = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 20
BOTTOM_PAD = 34
FONT = "SFMono-Regular, Consolas, 'Liberation Mono', Menlo, monospace"
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def load_data():
    with open("data/contributions.json") as f:
        return json.load(f)


def build_week_grid(days):
    """Bucket days into 53 columns x 7 rows keyed by (week_index, weekday)."""
    if not days:
        return {}, []
    parsed = []
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        parsed.append((dt, d["level"], d["count"]))
    parsed.sort(key=lambda t: t[0])

    first_sunday = parsed[0][0]
    while first_sunday.weekday() != 6:  # Sunday = 6 in Python (Mon=0)
        first_sunday -= timedelta(days=1)

    grid = {}
    for dt, level, count in parsed:
        delta_days = (dt - first_sunday).days
        week = delta_days // 7
        weekday = dt.weekday()
        weekday = (weekday + 1) % 7  # convert Mon=0 -> Sun=0 indexing
        grid[(week, weekday)] = {"date": dt, "level": level, "count": count}

    month_markers = []
    seen_months = set()
    for (week, weekday), cell in sorted(grid.items()):
        key = (cell["date"].year, cell["date"].month)
        if weekday == 0 and key not in seen_months:
            seen_months.add(key)
            month_markers.append((week, MONTH_LABELS[cell["date"].month - 1]))

    return grid, month_markers


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def make_svg(data, out_path="../contrib-heatmap.svg"):
    days = data.get("days", [])
    stats = data.get("stats", {})
    grid, month_markers = build_week_grid(days)

    weeks = max([w for (w, _) in grid.keys()], default=52) + 1 if grid else 53
    width = LEFT_PAD + weeks * (BOX + GAP)
    height = TOP_PAD + 7 * (BOX + GAP) + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">'
    )
    parts.append(
        f"<style>"
        f"text {{ font-family: {FONT}; font-size: 10px; fill: #8b949e; }}"
        f".foot {{ font-size: 11px; fill: #c9d1d9; }}"
        f"@keyframes reveal {{ from {{ opacity: 0; transform: translateY(-6px); }} "
        f"to {{ opacity: 1; transform: translateY(0); }} }}"
        f".cell {{ animation: reveal 0.35s cubic-bezier(.3,0,.2,1) both; }}"
        f"</style>"
    )
    parts.append(f'<rect width="100%" height="100%" fill="#0d1117"/>')

    # month labels
    for week, label in month_markers:
        x = LEFT_PAD + week * (BOX + GAP)
        parts.append(f'<text x="{x}" y="{TOP_PAD-6}">{label}</text>')

    # day-of-week labels
    for wd, label in DOW_LABELS.items():
        y = TOP_PAD + wd * (BOX + GAP) + BOX - 1
        parts.append(f'<text x="0" y="{y}">{label}</text>')

    # cells, diagonal stagger: order by (week + weekday)
    cells = []
    for (week, weekday), cell in grid.items():
        cells.append((week, weekday, cell))
    cells.sort(key=lambda t: (t[0] + t[1], t[0]))

    max_delay_unit = max([w + wd for (w, wd, _) in cells], default=1) or 1
    stagger_total = 1.6  # seconds for the whole reveal
    per_unit = stagger_total / max_delay_unit

    for week, weekday, cell in cells:
        x = LEFT_PAD + week * (BOX + GAP)
        y = TOP_PAD + weekday * (BOX + GAP)
        level = max(0, min(5, cell["level"]))
        color = PALETTE[level]
        delay = (week + weekday) * per_unit
        title = f'{cell["count"]} contributions on {cell["date"].strftime("%b %-d, %Y")}'
        parts.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2" '
            f'fill="{color}" style="animation-delay:{delay:.2f}s">'
            f'<title>{escape(title)}</title>'
            f"</rect>"
        )

    # legend
    legend_y = height - 20
    legend_x = width - LEFT_PAD - 6 * (BOX + 2) - 60
    parts.append(f'<text x="{legend_x}" y="{legend_y+9}">Less</text>')
    for i, color in enumerate(PALETTE):
        lx = legend_x + 32 + i * (BOX + 2)
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 32 + len(PALETTE)*(BOX+2) + 6}" y="{legend_y+9}">More</text>')

    # stats footer
    total = stats.get("total_last_year", 0)
    footer = f"{total:,} contributions in the last year"
    parts.append(f'<text x="{LEFT_PAD}" y="{height-6}" class="foot">{escape(footer)}</text>')

    parts.append("</svg>")
    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    data = load_data()
    make_svg(data)
