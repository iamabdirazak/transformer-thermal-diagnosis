"""Transformer elevation drawing: only what the model uses.

Run from the repository root: python -m src.visualization.drawing [light|dark]
The PNG is rendered from the SVG with: rsvg-convert -z 2 docs/plant.svg -o docs/plant.png
"""

import sys

W, H = 1200, 700
THEME = sys.argv[1] if len(sys.argv) > 1 else "light"
PALETTES = {
    "light": dict(bg="#F5F5F7", ink="#1D1D1F", line="#8A8A8F", sec="#6E6E73", accent="#5E8B3A", oil="#E3EFD6"),
    "dark": dict(bg="#242427", ink="#F5F5F7", line="#7C7C82", sec="#A1A1A6", accent="#8FB96A", oil="#2D3B23"),
}
P = PALETTES[THEME]
BG, INK, SEC, LINE, ACCENT, OIL = P["bg"], P["ink"], P["sec"], P["line"], P["accent"], P["oil"]

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
  f'font-family="Inter, SF Pro Text, Helvetica Neue, Arial">')
a(f'<rect width="{W}" height="{H}" rx="24" fill="{BG}"/>')


def line(x1, y1, x2, y2, c=LINE, w=1.2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"{d} stroke-linecap="round"/>')


def rect(x, y, w, h, fill="none", stroke=LINE, sw=1.6, rx=0):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def text(x, y, s, size=11, c=SEC, anchor="start", weight=400):
    a(f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def bubble(x, y, tag, num):
    a(f'<circle cx="{x}" cy="{y}" r="18" fill="{BG}" stroke="{LINE}" stroke-width="1.2"/>')
    text(x, y - 1, tag, 10.5, INK, "middle", 600)
    text(x, y + 11, num, 9.5, INK, "middle")


def arrow(x, y, direction):
    pts = {"up": f"{x-5},{y+5} {x},{y-6} {x+5},{y+5}", "down": f"{x-5},{y-5} {x},{y+6} {x+5},{y-5}"}[direction]
    a(f'<polygon points="{pts}" fill="{ACCENT}" fill-opacity="0.55"/>')


text(W / 2, 54, "Distribution Transformer", 27, INK, "middle", 600)
text(W / 2, 80, "100 kVA, 11/0.433 kV, oil-immersed with natural cooling", 13, SEC, "middle")

ground = 630
line(90, ground, 1110, ground, LINE, 1.2)
text(1110, ground + 22, "Plinth", 10.5, SEC, "end")

# tank: oil fills it to just below the cover
tx, ty, tw, th = 420, 330, 300, 280
a(f'<rect x="{tx}" y="{ty + 18}" width="{tw}" height="{th - 18}" fill="{OIL}"/>')
rect(tx, ty, tw, th, rx=6)
line(tx - 10, ty, tx + tw + 10, ty, LINE, 2.4)  # cover
for x in (tx + 30, tx + tw - 50):  # skid
    rect(x, ty + th, 20, ground - ty - th, sw=1.2)
# core and windings, dashed inside the tank
rect(tx + 70, ty + 70, 160, 170, sw=1.0)
for x in (tx + 95, tx + 165):
    a(f'<rect x="{x}" y="{ty + 90}" width="40" height="130" fill="none" stroke="{LINE}" stroke-width="1" stroke-dasharray="4 3"/>')
text(tx + tw / 2, ty + 262, "Core and windings", 10.5, SEC, "middle")

# radiators on both sides, oil circulating through them
for side in (-1, 1):
    x0 = tx - 110 if side < 0 else tx + tw + 20
    for i in range(5):
        rect(x0 + i * 18, ty + 40, 10, 200, fill=OIL, sw=1.1, rx=3)
    line(x0, ty + 40, x0 + 90, ty + 40, LINE, 1.6)
    line(x0, ty + 240, x0 + 90, ty + 240, LINE, 1.6)
    hx = tx if side < 0 else tx + tw
    line(hx, ty + 55, x0 + (90 if side < 0 else 0), ty + 55, LINE, 1.6)
    line(hx, ty + 225, x0 + (90 if side < 0 else 0), ty + 225, LINE, 1.6)
    arrow(x0 + 45 - 4, ty + 140, "down")
text(tx - 65, ty + 268, "Radiators", 10.5, SEC, "middle")
arrow(tx + tw / 2, ty + 52, "up")
text(tx + tw / 2 + 12, ty + 56, "Hot oil rises", 10.5, SEC)

# conservator on top
rect(tx + 10, ty - 150, 160, 46, rx=23)
line(tx + 150, ty - 104, tx + 150, ty, LINE, 1.6)
text(tx + 90, ty - 162, "Conservator", 10.5, SEC, "middle")

# bushings
for x in (tx + 50, tx + 90, tx + 130):
    for k in range(4):
        rect(x - 7 + k, ty - 50 + k * 12, 14 - 2 * k, 10, sw=1.0, rx=3)
text(tx + 34, ty - 20, "HV 11 kV", 10.5, SEC, "end")
for x in (tx + 200, tx + 230, tx + 260):
    rect(x - 5, ty - 26, 10, 26, sw=1.0, rx=3)

# instruments
pocket_x = tx + 180
line(pocket_x, ty, pocket_x, ty + 26, INK, 2.2)  # thermometer pocket in the top oil
line(pocket_x, ty, pocket_x, ty - 182, LINE, 1.0, "4 3")
bubble(pocket_x, ty - 200, "TT", "101")
text(pocket_x + 26, ty - 196, "Top oil", 10.5, INK)

lv = tx + 260  # LV side, out to the feeder
line(lv, ty - 26, lv, ty - 60, LINE, 1.6)
line(lv, ty - 60, 1010, ty - 60, LINE, 1.6)
a(f'<circle cx="900" cy="{ty - 60}" r="9" fill="none" stroke="{LINE}" stroke-width="1.2"/>')
line(900, ty - 69, 900, ty - 182, LINE, 1.0, "4 3")
bubble(900, ty - 200, "JT", "101")
text(926, ty - 196, "Load, kVA", 10.5, INK)
text(1010, ty - 70, "LV 433 V feeder", 10.5, SEC, "end")

# ambient sensor in a shaded screen beside the transformer
sx, sy = 980, 500
a(f'<polygon points="{sx-26},{sy-34} {sx},{sy-50} {sx+26},{sy-34}" fill="none" stroke="{LINE}" stroke-width="1.2"/>')
rect(sx - 20, sy - 34, 40, 40, sw=1.2)
line(sx, sy + 6, sx, ground, LINE, 1.2)
line(sx, sy - 14, sx - 60, sy - 14, LINE, 1.0, "4 3")
bubble(sx - 78, sy - 14, "TT", "102")
text(sx - 78, sy + 22, "Ambient", 10.5, INK, "middle")

a("</svg>")
suffix = "" if THEME == "light" else "-dark"
open(f"docs/plant{suffix}.svg", "w").write("\n".join(o))
