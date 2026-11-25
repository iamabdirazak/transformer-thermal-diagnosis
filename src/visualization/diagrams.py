"""Documentation diagrams: the model as a file, and how it works, in both themes.

The layout matches the earlier projects: a soft frame with a title, a
symmetric row of raised cards, each with an icon, a name and a short
description, and small arrows between them.
"""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch, Polygon
from matplotlib.path import Path as Shape
from PIL import Image

from src.visualization import style

DOCS = Path("docs")
CARD_W, CARD_H, GAP = 2.6, 3.4, 0.41
MARGIN = CARD_Y = 0.4
CARD_RADIUS, FRAME_RADIUS = 0.27, 0.38
HEIGHT = CARD_Y + CARD_H + 1.0
ICON_Y = CARD_Y + 2.25
NAME_Y, SUBTITLE_Y = CARD_Y + 1.05, CARD_Y + 0.65
MIDDLE = CARD_Y + CARD_H / 2

SURFACES = {  # card, highlight on accent, file page gradient, page rim, fold gradient, shadow strength
    "light": dict(card="#FFFFFF", highlight="#FFFFFF", page=["#E6E6EA", "#F4F4F6", "#FFFFFF"], rim="#D2D2D7",
                  fold=["#D8D8DD", "#EEEEF1"], shadow=0.25, deep="#3C5E22"),
    "dark": dict(card="#303034", highlight="#F1F8EA", page=["#2A2A2E", "#35353A", "#414147"], rim="#55555B",
                 fold=["#4A4A50", "#66666D"], shadow=1.0, deep="#33502A"),
}


class Canvas:
    def __init__(self, theme: str, width: float, height: float):
        self.colors, self.surface = style.apply(theme), SURFACES[theme]
        self.theme, self.width, self.height = theme, width, height
        self.figure, self.axis = plt.subplots(figsize=(width / 1.45, height / 1.45))
        self.axis.set_xlim(0, width)
        self.axis.set_ylim(0, height)
        self.axis.set_aspect("equal")
        self.axis.axis("off")
        self.rounded(0, 0, width, height, self.colors["background"], FRAME_RADIUS, z=1)

    def rounded(self, x, y, w, h, color, radius=0.12, z=3, alpha=1.0):
        self.axis.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radius}",
                                           facecolor=color, edgecolor="none", alpha=alpha, zorder=z))

    def dot(self, x, y, r, color, alpha=1.0, z=5):
        self.axis.add_patch(Circle((x, y), r, facecolor=color, edgecolor="none", alpha=alpha, zorder=z))

    def line(self, xs, ys, color, width=2.2, z=5, dash=None, alpha=1.0):
        self.axis.plot(xs, ys, color=color, linewidth=width, solid_capstyle="round", dash_capstyle="round",
                       linestyle=dash or "-", alpha=alpha, zorder=z)

    def text(self, x, y, value, size, color, weight="regular"):
        self.axis.text(x, y, value, ha="center", va="center", fontsize=size, fontweight=weight, color=color, zorder=6)

    def save(self, name: str):
        style.save(self.figure, DOCS, name, self.theme, panel=False)


# Icons, each centred on (cx, cy) ---------------------------------------------

def icon_input(c: Canvas, cx, cy):
    """Readings arriving step after step: stacked frames, each holding a signal."""
    for offset, alpha in ((-0.28, 0.3), (-0.14, 0.55), (0.0, 1.0)):
        c.rounded(cx - 0.5 + offset, cy - 0.34 - offset, 0.95, 0.68, c.colors["strong"], 0.12, z=3 + alpha, alpha=alpha)
    t = np.linspace(0, 1, 80)
    c.line(cx - 0.32 + 0.6 * t, cy + 0.12 * np.sin(2 * np.pi * 1.5 * t) - 0.02, c.surface["highlight"], 2.2, z=7)


def icon_physics(c: Canvas, cx, cy):
    """A load step and the oil following it: the first-order rise to its new level."""
    t = np.linspace(0, 1, 80)
    c.line([cx - 0.62, cx - 0.2, cx - 0.2, cx + 0.62], [cy - 0.36, cy - 0.36, cy + 0.32, cy + 0.32],
           c.colors["base"], 1.8, dash=(0, (2, 2)))
    oil = cy - 0.36 + 0.68 * (1 - np.exp(-4.2 * t))
    c.line(cx - 0.2 + 0.82 * t, oil, c.colors["strong"], 2.6, z=6)
    c.line([cx - 0.62, cx - 0.2], [cy - 0.36, cy - 0.36], c.colors["strong"], 2.6, z=6)
    c.dot(cx - 0.2, cy - 0.36, 0.1, c.colors["strong"], z=7)
    c.dot(cx - 0.2, cy - 0.36, 0.045, c.surface["highlight"], z=8)


def icon_learned(c: Canvas, cx, cy):
    """Healthy measurements, and the smooth gap the learned unit fits through them."""
    rng = np.random.default_rng(4)
    xs = np.linspace(-0.55, 0.55, 12)
    for x in xs:
        c.dot(cx + x, cy + 0.32 * x - 0.18 * x**2 + 0.07 * rng.standard_normal(), 0.055, c.colors["soft"], z=4)
    x = np.linspace(-0.62, 0.62, 60)
    c.line(cx + x, cy + 0.32 * x - 0.18 * x**2, c.colors["strong"], 2.6, z=6)


def icon_residuals(c: Canvas, cx, cy):
    """Measured minus expected: small bars about zero, one growing as a fault grows."""
    heights = (0.08, -0.06, 0.1, -0.05, 0.2, 0.36, 0.52)
    for i, h in enumerate(heights):
        x = cx - 0.6 + i * 0.18
        color = c.colors["strong"] if i >= 4 else c.colors["soft"]
        c.rounded(x, cy - 0.3 + min(0, h), 0.12, max(abs(h), 0.05), color, 0.04, z=4)
    c.line([cx - 0.66, cx + 0.66], [cy - 0.3, cy - 0.3], c.colors["secondary"], 1.0, z=3)


def icon_health(c: Canvas, cx, cy):
    """A gauge read in engineering units: the arc of health still left."""
    a = np.radians(np.linspace(210, -30, 80))
    c.line(cx + 0.5 * np.cos(a), cy - 0.05 + 0.5 * np.sin(a), c.colors["faint"] if c.theme == "light" else c.colors["soft"], 7, z=4)
    a = np.radians(np.linspace(210, 40, 60))
    c.line(cx + 0.5 * np.cos(a), cy - 0.05 + 0.5 * np.sin(a), c.colors["strong"], 7, z=5)
    tip = np.radians(40)
    c.line([cx, cx + 0.32 * np.cos(tip)], [cy - 0.05, cy - 0.05 + 0.32 * np.sin(tip)], c.colors["base"], 2.4, z=6)
    c.dot(cx, cy - 0.05, 0.08, c.colors["strong"], z=7)


def icon_advisory(c: Canvas, cx, cy):
    """A health line crossing its threshold, held for a while, and the advisory raised after it."""
    c.rounded(cx + 0.08, cy - 0.45, 0.55, 0.9, c.colors["faint"] if c.theme == "light" else c.colors["soft"], 0.08, z=3,
              alpha=0.9 if c.theme == "light" else 0.45)
    c.line([cx - 0.62, cx + 0.62], [cy - 0.02, cy - 0.02], c.colors["secondary"], 1.4, z=4, dash=(0, (2, 2)))
    t = np.linspace(0, 1, 60)
    c.line(cx - 0.62 + 1.24 * t, cy - 0.38 + 0.72 * t**2, c.colors["strong"], 2.6, z=6)
    c.dot(cx + 0.08, cy - 0.02, 0.08, c.colors["strong"], z=7)


def architecture(theme: str) -> None:
    cards = [
        ("Input", "Load, ambient, top oil", icon_input),
        ("Thermal Physics", "IEC 60076-7 top oil", icon_physics),
        ("Learned Twin", "This unit's own parameters", icon_learned),
        ("Residuals", "Measured minus twin", icon_residuals),
        ("Health", "Least squares over a week", icon_health),
        ("Advisory", "Thresholds with deadband", icon_advisory),
    ]
    width = len(cards) * CARD_W + (len(cards) - 1) * GAP + 2 * MARGIN
    c = Canvas(theme, width, HEIGHT)
    c.text(width / 2, HEIGHT - 0.5, "Model Architecture", 13, c.colors["ink"], "medium")
    for index, (name, subtitle, draw) in enumerate(cards):
        x = MARGIN + index * (CARD_W + GAP)
        centre = x + CARD_W / 2
        c.rounded(x, CARD_Y, CARD_W, CARD_H, c.surface["card"], CARD_RADIUS, z=2)
        draw(c, centre, ICON_Y)
        c.text(centre, NAME_Y, name, 10, c.colors["ink"], "medium")
        c.text(centre, SUBTITLE_Y, subtitle, 7.4, c.colors["secondary"])
        if index:
            mid = x - GAP / 2
            c.axis.add_patch(Polygon([[mid - 0.07, MIDDLE - 0.12], [mid - 0.07, MIDDLE + 0.12], [mid + 0.09, MIDDLE]],
                                     facecolor=c.colors["secondary"], edgecolor="none", zorder=3))
    c.save("architecture")


# The model as a file ---------------------------------------------------------

def gradient(c: Canvas, patch, colors, angle=90, z=3):
    """Fill a patch with a linear gradient; angle 90 runs bottom to top."""
    c.axis.add_patch(patch)
    patch.set_facecolor("none")
    patch.set_edgecolor("none")
    x0, y0, w, h = patch.get_path().transformed(patch.get_patch_transform()).get_extents().bounds
    t = np.radians(angle)
    gx, gy = np.meshgrid(np.linspace(0, 1, 256), np.linspace(0, 1, 256))
    ramp = gx * np.cos(t) + gy * np.sin(t)
    ramp = (ramp - ramp.min()) / (ramp.max() - ramp.min())
    image = c.axis.imshow(ramp, extent=(x0, x0 + w, y0, y0 + h), origin="lower", zorder=z,
                          cmap=LinearSegmentedColormap.from_list("", colors), interpolation="bicubic")
    image.set_clip_path(patch)


def page(x, y, w, h, fold, radius):
    """A document outline with rounded corners and a folded top-right corner."""
    points = []
    for centre, start, end in (((x + radius, y + radius), 180, 270), ((x + w - radius, y + radius), 270, 360)):
        points += [(centre[0] + radius * np.cos(a), centre[1] + radius * np.sin(a))
                   for a in np.radians(np.linspace(start, end, 12))]
    points += [(x + w, y + h - fold), (x + w - fold, y + h)]
    centre = (x + radius, y + h - radius)
    points += [(centre[0] + radius * np.cos(a), centre[1] + radius * np.sin(a)) for a in np.radians(np.linspace(90, 180, 12))]
    return PathPatch(Shape(points + [points[0]], closed=True))


def onnx_mark(c: Canvas) -> np.ndarray:
    """The ONNX mark from docs/onnx.png, without its wordmark, recoloured in the accent."""
    source = np.asarray(Image.open(DOCS / "onnx.png").convert("RGBA")).astype(float) / 255
    mark = source[:575]
    rows, columns = np.where(mark[..., 3] > 0.05)
    mark = mark[rows.min():rows.max() + 1, columns.min():columns.max() + 1]
    lightness, alpha = mark[..., :3].mean(axis=2), mark[..., 3]
    line = lightness < 0.5
    deep, rich = (c.surface["deep"], c.colors["strong"]) if c.theme == "light" else (c.surface["deep"], c.colors["base"])
    facets = LinearSegmentedColormap.from_list("", [deep, rich, c.colors["base"] if c.theme == "light" else c.colors["strong"]])
    shade = np.clip((lightness - 0.6) / 0.38, 0, 1)
    image = np.empty_like(mark)
    edge = "#FFFFFF" if c.theme == "light" else "#E2F0D4"
    image[..., :3] = np.where(line[..., None], matplotlib.colors.to_rgb(edge), facets(shade)[..., :3])
    image[..., 3] = np.where(line, alpha, alpha * 0.92)
    return image


def model_file(theme: str) -> None:
    """The released model shown as what it is: a single ONNX file."""
    width, height = 6 * CARD_W + 5 * GAP + 2 * MARGIN, 7.2
    c = Canvas(theme, width, height)
    w, h, fold = 2.55, 3.4, 0.62
    x, y, cx = width / 2 - w / 2, 2.5, width / 2

    for spread, alpha in ((0.32, 0.04), (0.2, 0.06), (0.1, 0.09), (0.03, 0.14)):
        shadow = page(x - spread, y - spread - 0.12, w + 2 * spread, h + 2 * spread, fold + spread, 0.2 + spread)
        shadow.set(facecolor="black", edgecolor="none", alpha=alpha * c.surface["shadow"], zorder=2)
        c.axis.add_patch(shadow)
    gradient(c, page(x, y, w, h, fold, 0.2), c.surface["page"], z=3)
    rim = page(x, y, w, h, fold, 0.2)
    rim.set(facecolor="none", edgecolor=c.surface["rim"], linewidth=1, zorder=4)
    c.axis.add_patch(rim)
    flap = PathPatch(Shape([(x + w - fold, y + h), (x + w - fold, y + h - fold + 0.1), (x + w - fold + 0.1, y + h - fold),
                            (x + w, y + h - fold), (x + w - fold, y + h)], closed=True))
    gradient(c, flap, c.surface["fold"], angle=45, z=4)

    mark = onnx_mark(c)
    size, label = 1.3, 0.3
    aspect = mark.shape[0] / mark.shape[1]
    block = size * aspect + 0.36 + label
    top = y + h * 0.47 + block / 2
    c.axis.imshow(mark, extent=(cx - size / 2, cx + size / 2, top - size * aspect, top), zorder=6, interpolation="lanczos")
    c.text(cx, top - block + label / 2, "ONNX", 15, "#8E8E93", "medium")

    edge = json.loads(Path("reports/results.json").read_text())["edge"]
    c.text(cx, 1.7, "Transformer Thermal Model", 14, c.colors["ink"], "semibold")
    c.text(cx, 1.25, f"transformer.onnx  ·  3 learned parameters  ·  {edge['size_kb']:.1f} KB", 9, c.colors["secondary"])
    c.save("model")


if __name__ == "__main__":
    for theme in ("light", "dark"):
        model_file(theme)
        architecture(theme)
