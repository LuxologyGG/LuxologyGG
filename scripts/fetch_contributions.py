"""
Step 5a — Get real contribution data, no token.

GitHub serves the contribution calendar as public HTML at
https://github.com/users/<username>/contributions -- the same fragment the
profile page itself uses. Fetch it, parse the day cells, and write
data/contributions.json with raw days plus derived stats.

Usage:
    python scripts/fetch_contributions.py [username]
"""
import json
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

USERNAME_DEFAULT = "luxologygg"
URL = "https://github.com/users/{user}/contributions"

COUNT_RE = re.compile(r"^(No|\d[\d,]*)\s+contributions?", re.IGNORECASE)


def parse_count(tooltip_text: str) -> int:
    """'No contributions on...' -> 0, 'N contributions on...' -> N."""
    if not tooltip_text:
        return 0
    m = COUNT_RE.match(tooltip_text.strip())
    if not m:
        return 0
    head = m.group(1)
    if head.lower() == "no":
        return 0
    return int(head.replace(",", ""))


def fetch(username: str):
    resp = requests.get(
        URL.format(user=username),
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # counts live in sibling <tool-tip for="<cell-id>">N contributions on...</tool-tip>
    tooltip_by_id = {}
    for tip in soup.select("tool-tip[for]"):
        tooltip_by_id[tip.get("for")] = tip.get_text(strip=True)

    days = []
    cells = soup.select("td.ContributionCalendar-day")
    for cell in cells:
        date = cell.get("data-date")
        level = cell.get("data-level")
        if date is None:
            continue
        if level is None:
            level = 0
        cell_id = cell.get("id")
        tooltip_text = tooltip_by_id.get(cell_id, "")
        count = parse_count(tooltip_text)
        days.append(
            {
                "date": date,
                "level": int(level),
                "count": count,
            }
        )

    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days):
    total = sum(d["count"] for d in days)

    # current streak (from most recent day backwards)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"], default=None)

    monthly = {}
    for d in days:
        month = d["date"][:7]
        monthly[month] = monthly.get(month, 0) + d["count"]

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly": monthly,
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else USERNAME_DEFAULT
    try:
        days = fetch(username)
        if not days:
            raise ValueError("no contribution cells parsed")
    except Exception as e:
        print(f"fetch failed ({e}); writing empty calendar so pipeline still runs")
        days = []

    stats = derive_stats(days) if days else {
        "total_last_year": 0, "current_streak": 0, "longest_streak": 0,
        "best_day": None, "monthly": {},
    }

    out = {
        "username": username,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    with open("data/contributions.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote data/contributions.json ({len(days)} days, "
          f"{stats['total_last_year']} contributions)")
