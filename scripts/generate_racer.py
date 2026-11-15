"""Contribution racetrack with a gold racing car and smoke at the turns."""
import argparse
import math
from pathlib import Path
import xml.etree.ElementTree as ET
from generate_train import fetch_calendar, render as train_svg

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def render(calendar, username):
    root = ET.fromstring(train_svg(calendar, username))
    for node in list(root):
        if node.get('class') == 'train':
            root.remove(node)
    root.find(f'{{{NS}}}title').text = f"{username}'s contribution racer"
    root.find(f'{{{NS}}}desc').text = 'A gold racing car drives through the contribution calendar, drifting and leaving smoke at turns.'
    root.find(f'{{{NS}}}style').text = '@media(prefers-reduced-motion:reduce){.racer{display:none}}'
    root.find(f'{{{NS}}}text').text = f"COMMIT GRAND PRIX · {calendar['totalContributions']} contributions"
    paths = root.findall(f'{{{NS}}}path')
    route = paths[0].get('d')
    paths[0].set('stroke-width', '19')
    paths[0].set('stroke', '#202833')
    paths[1].set('stroke', '#647080')
    paths[1].set('stroke-dasharray', '3 8')
    # Compute the same cubic turn's length to synchronize drift with motion.
    curve = []
    for i in range(101):
        t = i / 100
        curve.append((42*t*(1-t), 28*(3*t*t-2*t*t*t)))
    bend = sum(math.dist(a, b) for a, b in zip(curve, curve[1:]))
    straight = (len(calendar['weeks']) - 1) * 20
    def cubic_length(p0, p1, p2, p3):
        points = [tuple((1-t)**3*p0[j]+3*(1-t)**2*t*p1[j]+3*(1-t)*t*t*p2[j]+t**3*p3[j] for j in (0,1)) for t in [i/100 for i in range(101)]]
        return sum(math.dist(a,b) for a,b in zip(points,points[1:]))
    tail = cubic_length((0,224),(24,224),(24,252),(0,252))
    back = cubic_length((32,252),(2,252),(2,56),(32,56))
    length = 8*straight + 6*bend + tail + back
    drift = [(0, '0')]
    smoke = [(0, '0')]
    for row in range(6):
        start = ((row+1)*straight + row*bend)/length
        end = start + bend/length
        drift.extend([(start, '0'), ((start+end)/2, '-32'), (end, '0')])
        smoke.extend([(start,'1'),(end,'0')])
    drift.append((1,'0'))
    smoke.append((1,'0'))
    def animation(attr, events, extra=''):
        tag = 'animateTransform' if attr == 'transform' else 'animate'
        return f'<{tag} attributeName="{attr}" {extra} values="{";".join(v for _,v in events)}" keyTimes="{";".join(f"{t:.7f}" for t,_ in events)}" dur="22s" repeatCount="indefinite"/>'
    car = f'''<g xmlns="{NS}" class="racer">
<animateMotion path="{route}" dur="22s" repeatCount="indefinite" rotate="auto"/>
<g>{animation('transform', drift, 'type="rotate"')}
<g opacity="0">{animation('opacity',smoke,'calcMode="discrete"')}
<circle cx="-17" cy="-7" r="5" fill="#a8b3c2" opacity=".55"><animate attributeName="r" values="3;9" dur=".4s" repeatCount="indefinite"/><animate attributeName="opacity" values=".65;0" dur=".4s" repeatCount="indefinite"/></circle>
<circle cx="-21" cy="7" r="6" fill="#a8b3c2"><animate attributeName="r" values="4;11" dur=".55s" repeatCount="indefinite"/><animate attributeName="opacity" values=".5;0" dur=".55s" repeatCount="indefinite"/></circle>
</g>
<path d="M-15-5L-25-3M-15 5L-25 3" stroke="#f0883e" stroke-width="2"/>
<rect x="-11" y="-11" width="7" height="5" rx="1" fill="#010409"/>
<rect x="5" y="-11" width="7" height="5" rx="1" fill="#010409"/>
<rect x="-11" y="6" width="7" height="5" rx="1" fill="#010409"/>
<rect x="5" y="6" width="7" height="5" rx="1" fill="#010409"/>
<path d="M-14-6L4-8L15-5L17 0L15 5L4 8L-14 6Z" fill="#d4a017" stroke="#f2cc60" stroke-width="1.3"/>
<path d="M-4-5L5-4L7 0L5 4L-4 5Z" fill="#0d2538" stroke="#79c0ff" stroke-width=".8"/>
<path d="M-12 0H-5M9 0H16" stroke="#fff1b8" stroke-width="2"/>
<path d="M-14-9V9" stroke="#f2cc60" stroke-width="3"/>
<path d="M14-4H16M14 4H16" stroke="#fff" stroke-width="2"/>
</g></g>'''
    root.append(ET.fromstring(car))
    footer = ET.SubElement(root, f'{{{NS}}}text', {'x':'24','y':'272','fill':'#8b949e','font-family':'monospace','font-size':'10'})
    footer.text = 'BUILD. COMMIT. DRIFT. REPEAT.'
    return ET.tostring(root, encoding='unicode')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', required=True)
    parser.add_argument('--output', default='dist/contribution-racer.svg')
    args = parser.parse_args()
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(fetch_calendar(args.username), args.username), encoding='utf-8')
    print(f'Generated {dest}')
