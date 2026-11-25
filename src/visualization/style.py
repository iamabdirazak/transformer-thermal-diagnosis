"""One visual language for every figure, in a light and a dark theme.

The accent is pistachio, in shades named by emphasis. Neutral tones
come from Apple's light and dark appearances.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

THEMES = {
    "light": {
        "background": "#F5F5F7", "ink": "#1D1D1F", "secondary": "#6E6E73", "hairline": "#D2D2D7",
        "strong": "#5E8B3A", "base": "#8FB96A", "soft": "#BBD69E", "faint": "#E3EFD6",
    },
    "dark": {
        "background": "#242427", "ink": "#F5F5F7", "secondary": "#A1A1A6", "hairline": "#3A3A3D",
        "strong": "#B7DD93", "base": "#8FB96A", "soft": "#5D7F40", "faint": "#2D3B23",
    },
}

PADDING = 0.3  # inches of background around the content
ROUNDING = 0.018  # corner radius as a share of panel width


def apply(theme: str) -> dict:
    colors = THEMES[theme]
    plt.rcParams.update({
        "font.family": ["Inter"],
        "font.size": 9,
        "text.color": colors["ink"],
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.titlepad": 12,
        "axes.labelcolor": colors["secondary"],
        "axes.labelsize": 8.5,
        "axes.edgecolor": colors["hairline"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.spines.left": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": colors["hairline"],
        "grid.linewidth": 0.6,
        "xtick.color": colors["secondary"],
        "ytick.color": colors["secondary"],
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "xtick.major.size": 0,
        "ytick.major.size": 0,
        "legend.frameon": False,
        "figure.dpi": 200,
    })
    return colors


def save(figure, directory: Path, name: str, theme: str, panel: bool = True) -> None:
    """Save as SVG and PNG on one rounded panel, transparent beyond its corners.

    Diagrams that draw their own rounded frame pass panel=False.
    """
    colors = THEMES[theme]
    figure.canvas.draw()
    content = figure.get_tightbbox(figure.canvas.get_renderer())
    if panel:
        content = content.padded(PADDING)
    width, height = figure.get_size_inches()
    if panel:
        figure.add_artist(FancyBboxPatch(
            (content.x0 / width, content.y0 / height), content.width / width, content.height / height,
            boxstyle=f"round,pad=0,rounding_size={ROUNDING * content.width / width}", mutation_aspect=width / height,
            transform=figure.transFigure, facecolor=colors["background"], edgecolor="none", zorder=-10,
        ))
    figure.patch.set_alpha(0)
    for axis in figure.axes:
        axis.patch.set_alpha(0)
    directory.mkdir(parents=True, exist_ok=True)
    suffix = "" if theme == "light" else "-dark"
    for extension in ("svg", "png"):
        figure.savefig(directory / f"{name}{suffix}.{extension}", bbox_inches=content, pad_inches=0, transparent=True)
    plt.close(figure)


def legend(figure, items: list[tuple[str, str]], colors: dict) -> None:
    """One legend, top right, as short coloured lines."""
    from matplotlib.lines import Line2D

    handles = [Line2D([], [], color=color, linewidth=1.8, solid_capstyle="round") for color, _ in items]
    figure.legend(handles, [label for _, label in items], loc="lower right", bbox_to_anchor=(1.0, 1.0),
                  ncol=len(items), fontsize=8, handlelength=1.6, columnspacing=1.6, handletextpad=0.6,
                  labelcolor=colors["secondary"])
