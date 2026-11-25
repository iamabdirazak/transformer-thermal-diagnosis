"""Fault signatures: what each fault at severity 1 does to the steady oil rise."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.data.simulate import UNIT
from src.plant.faults import apply
from src.visualization import style


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    load = np.linspace(0, 1.4, 200)
    healthy = UNIT.rise(load)
    cases = ((apply(UNIT, "cooling", 1.0), colors["strong"], "Cooling degraded"),
             (apply(UNIT, "losses", 1.0), colors["base"], "Extra internal loss"))
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    axes[0].plot(load, healthy, color=colors["secondary"], linewidth=1.6)
    for unit, color, _ in cases:
        axes[0].plot(load, unit.rise(load), color=color, linewidth=1.8)
        axes[1].plot(load, unit.rise(load) - healthy, color=color, linewidth=1.8)
    axes[0].set_title("Steady Top-Oil Rise")
    axes[0].set_ylabel("K above ambient")
    axes[1].set_title("Added Rise")
    axes[1].set_ylabel("K")
    for axis in axes:
        axis.set_xlabel("Load factor K, per unit of rating")
        axis.set_xlim(0, 1.4)
        axis.set_ylim(bottom=0)
    style.legend(figure, [(colors["secondary"], "Healthy")] + [(c, label) for _, c, label in cases], colors)
    figure.tight_layout(w_pad=2.5)
    style.save(figure, directory, "faults", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("reports/figures"))
