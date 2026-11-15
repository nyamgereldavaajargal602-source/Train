"""A contribution collector robot; standalone animated SVG with no JavaScript."""
import argparse
from pathlib import Path
from xml.sax.saxutils import escape
from generate_train import fetch_calendar


def render(calendar, username):
    weeks = calendar['weeks']
    width = 64 + len(weeks) * 20
    colors = ['#18212d', '#0e4429', '#006d32', '#26a641', '#39d353']
    levels = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE']
    cells = [(c, d) for c, w in enumerate(weeks) for d in w['contributionDays']]
    active = sorted(((c, d) for c, d in cells if d['contributionCount']),
                    key=lambda item: (item[1]['weekday'], item[0] if item[1]['weekday'] % 2 == 0 else -item[0]))
    points = [(0, 32, 64)]
    collected, happy = {}, []
    clock = 0
    for c, day in active:
        x, y = 32 + c * 20, 64 + day['weekday'] * 28
        clock += .65
        points.append((clock, x, y))
        collected[c, day['weekday']] = clock
        celebrate = levels.index(day['contributionLevel']) >= 3
        if celebrate:
            happy.append((clock, clock + 1.1))
        clock += 1.1 if celebrate else .22
        points.append((clock, x, y))
    clock += 1.2
    points.append((clock, 32, 64))
    clock += 1.5
    points.append((clock, 32, 64))
    duration = clock

    def animate(attribute, events, discrete=False, transform=None):
        times = ';'.join(f'{t/duration:.7f}' for t, _ in events)
        values = ';'.join(str(v) for _, v in events)
        tag = 'animateTransform' if transform else 'animate'
        extra = f' type="{transform}"' if transform else ''
        mode = 'discrete' if discrete else 'linear'
        return f'<{tag} attributeName="{attribute}"{extra} values="{values}" keyTimes="{times}" calcMode="{mode}" dur="{duration:.3f}s" repeatCount="indefinite"/>'

    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 288" role="img" aria-labelledby="title desc">
<title id="title">{escape(username)}'s contribution collector</title>
<desc id="desc">A little robot collects active contribution cells and jumps with joy at busy days. {calendar['totalContributions']} contributions in the last year.</desc>
<rect width="100%" height="100%" rx="16" fill="#0d1117"/>
<style>@media(prefers-reduced-motion:reduce){{.robot,.effects{{display:none}}.cell{{opacity:1!important}}}}</style>
<text x="24" y="26" font-family="monospace" font-size="12" fill="#f2cc60">LITTLE COMMIT COLLECTOR</text>
<text x="{width-24}" y="26" text-anchor="end" font-family="monospace" font-size="11" fill="#8b949e">{calendar['totalContributions']} contributions</text>''']
    for c, d in cells:
        x, y = 32 + c * 20, 64 + d['weekday'] * 28
        color = colors[levels.index(d['contributionLevel'])]
        label = escape(f"{d['date']}: {d['contributionCount']} contributions")
        parts.append(f'<rect x="{x-7}" y="{y-7}" width="14" height="14" rx="3" fill="#18212d"/>')
        parts.append(f'<rect class="cell" x="{x-7}" y="{y-7}" width="14" height="14" rx="3" fill="{color}"><title>{label}</title>')
        t = collected.get((c, d['weekday']))
        if t is not None:
            parts.append(animate('opacity', [(0, 1), (t, .12), (duration, .12)], True))
        parts.append('</rect>')
        if t is not None:
            parts.append(f'<g class="effects" transform="translate({x} {y})" opacity="0">')
            parts.append(animate('opacity', [(0, 0), (t, 1), (t+.2, 0), (duration, 0)], True))
            parts.append('<path d="M-12 0H-8 M8 0H12 M0-12V-8 M0 8V12" stroke="#f2cc60" stroke-width="2"/></g>')
    parts.append('<g class="robot">')
    parts.append(animate('transform', [(t, f'{x} {y}') for t, x, y in points], transform='translate'))
    bounce = [(0, '0 0')]
    joy = [(0, 0)]
    for start, end in happy:
        bounce.extend([(start, '0 0'), (start+.23, '0 -12'), (start+.46, '0 0'), (start+.7, '0 -7'), (end, '0 0')])
        joy.extend([(start, 1), (end, 0)])
    bounce.append((duration, '0 0'))
    joy.append((duration, 0))
    parts.append('<g>')
    parts.append(animate('transform', bounce, transform='translate'))
    parts.append('''<ellipse cx="0" cy="14" rx="13" ry="3" fill="#010409" opacity=".5"/>
<path d="M-7 8V12 M7 8V12" stroke="#8b949e" stroke-width="5" stroke-linecap="round"/>
<rect x="-9" y="-2" width="18" height="12" rx="4" fill="#d4a017" stroke="#f2cc60"/>
<path d="M-12 1L-15 6 M12 1L15-4" stroke="#f2cc60" stroke-width="3" stroke-linecap="round"/>
<path d="M0-15V-20" stroke="#8b949e" stroke-width="2"/>
<circle cy="-21" r="2.5" fill="#56d364"/>
<rect x="-13" y="-16" width="26" height="17" rx="6" fill="#b7c9dc" stroke="#e6edf3"/>
<rect x="-10" y="-13" width="20" height="11" rx="4" fill="#0d1117"/>
<g fill="#56d364"><rect x="-7" y="-10" width="4" height="4" rx="1"/><rect x="3" y="-10" width="4" height="4" rx="1"/></g>
<rect x="-3" y="3" width="6" height="3" rx="1" fill="#56d364"/>
<g opacity="0">''')
    parts.append(animate('opacity', joy, True))
    parts.append('''<rect x="-10" y="-13" width="20" height="11" rx="4" fill="#0d1117"/>
<path d="M-7-7L-5-10L-3-7 M3-7L5-10L7-7" fill="none" stroke="#56d364" stroke-width="2" stroke-linecap="round"/>
<path d="M-21-15h6m-3-3v6 M17-23h8m-4-4v8 M20-4h5m-2.5-2.5v5" stroke="#f2cc60" stroke-width="2"/>
<text x="0" y="-32" text-anchor="middle" font-family="monospace" font-size="10" fill="#f2cc60">+ XP!</text>
</g></g></g>
<text x="24" y="272" font-family="monospace" font-size="10" fill="#8b949e">Collect commits. Celebrate progress.</text>
</svg>''')
    return '\n'.join(parts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default='nyamgereldavaajargal602-source')
    parser.add_argument('--output', default='dist/contribution-robot.svg')
    args = parser.parse_args()
    calendar = fetch_calendar(args.username)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(calendar, args.username), encoding='utf-8')
    print(f'Generated {dest}')
