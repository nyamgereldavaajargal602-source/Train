"""Generate a self-contained contribution train SVG (Python standard library only)."""

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


def fetch_calendar(username):
    query = """query($login: String!) {
      user(login: $login) { contributionsCollection { contributionCalendar {
        totalContributions weeks { contributionDays {
          date weekday contributionCount contributionLevel
        } }
      } } }
    }"""
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": username}}).encode(),
        headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
                 "Content-Type": "application/json", "User-Agent": "contribution-train"},
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(result["errors"])
    return result["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(calendar, username):
    colors = {"NONE": "#161b22", "FIRST_QUARTILE": "#0e4429",
              "SECOND_QUARTILE": "#006d32", "THIRD_QUARTILE": "#26a641",
              "FOURTH_QUARTILE": "#39d353"}
    weeks = calendar["weeks"]
    width = 64 + len(weeks) * 20
    right = 32 + (len(weeks) - 1) * 20
    # Seven connected rows; the return track runs below the calendar.
    route = "M 32 56"
    for row in range(7):
        end = right if row % 2 == 0 else 32
        route += f" H {end}"
        if row < 6:
            bend = end + (14 if row % 2 == 0 else -14)
            y = 56 + row * 28
            route += f" C {bend} {y} {bend} {y+28} {end} {y+28}"
    route += f" C {right+24} 224 {right+24} 252 {right} 252 H 32 C 2 252 2 56 32 56 Z"
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 280" role="img" aria-labelledby="title desc">
<title id="title">{escape(username)}'s contribution train</title>
<desc id="desc">A gold locomotive and three green carriages travel through the last year's contribution calendar. {calendar['totalContributions']} contributions.</desc>
<rect width="100%" height="100%" rx="12" fill="#0d1117"/>
<style>@media (prefers-reduced-motion: reduce) {{ .train {{ display:none }} }}</style>
<text x="24" y="25" fill="#8b949e" font-family="monospace" font-size="12">CONTRIBUTION EXPRESS · {calendar['totalContributions']} contributions</text>
<path d="{route}" fill="none" stroke="#26303b" stroke-width="3"/>
<path d="{route}" fill="none" stroke="#0d1117" stroke-width="1" stroke-dasharray="2 5"/>''']
    for column, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x, y = 32 + column * 20, 56 + day["weekday"] * 28
            label = escape(f"{day['date']}: {day['contributionCount']} contributions")
            parts.append(f'<rect x="{x-7}" y="{y-7}" width="14" height="14" rx="3" fill="{colors[day["contributionLevel"]]}"><title>{label}</title></rect>')
    # Each carriage follows exactly the same track, offset by one carriage length.
    duration = 72
    # Approximate track length sets consistent spacing across 52/53-week calendars.
    length = 8 * (right - 32) + 440
    delay = 24 / length * duration
    for index in range(3, -1, -1):
        begin = -8 + index * delay
        parts.append(f'<g class="train"><animateMotion path="{route}" dur="{duration}s" begin="{begin:.4f}s" rotate="auto" repeatCount="indefinite"/>')
        if index == 0:
            parts.append('''<path d="M-11 5 H11 L14 2 L10-1 V-5 H5 V-9 H1 V-4 H-2 V-9 H-11 Z" fill="#d4a017" stroke="#f2cc60" stroke-width="1"/>
<rect x="-9" y="-7" width="5" height="5" rx="1" fill="#0d1117"/>
<circle cx="8" cy="-12" r="2" fill="#8b949e"><animate attributeName="cy" values="-12;-22" dur="1.4s" repeatCount="indefinite"/><animate attributeName="opacity" values=".7;0" dur="1.4s" repeatCount="indefinite"/><animate attributeName="r" values="2;5" dur="1.4s" repeatCount="indefinite"/></circle>''')
        else:
            parts.append('<path d="M-13 3 H13" stroke="#8b949e" stroke-width="2"/><rect x="-10" y="-7" width="20" height="12" rx="3" fill="#238636" stroke="#56d364"/><path d="M-6-3 H-2 M2-3 H6" stroke="#aff5b4" stroke-width="3"/>')
        parts.append('<circle cx="-6" cy="6" r="3" fill="#0d1117" stroke="#8b949e"/><circle cx="7" cy="6" r="3" fill="#0d1117" stroke="#8b949e"/></g>')
    parts.append('</svg>')
    return '\n'.join(parts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="mubabne")
    parser.add_argument("--output", default="dist/contribution-train.svg")
    parser.add_argument("--demo", action="store_true", help="Use sample data for a local preview only")
    args = parser.parse_args()
    if args.demo:
        levels = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
        calendar = {"totalContributions": 0, "weeks": []}
        for week in range(53):
            days = []
            for day in range(7):
                count = (week * 7 + day * 3) % 5 if week % 4 == 0 else 0
                calendar["totalContributions"] += count
                days.append({"weekday": day, "date": "Sample data", "contributionCount": count, "contributionLevel": levels[count]})
            calendar["weeks"].append({"contributionDays": days})
    else:
        calendar = fetch_calendar(args.username)
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(calendar, args.username), encoding="utf-8")
    print(f"Generated {destination}")
