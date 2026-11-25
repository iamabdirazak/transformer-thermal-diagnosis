"""The field data: real load and ambient through the record, gaps shaded."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.visualization import style


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    frame = pd.read_parquet("data/profile.parquet").set_index("time")
    daily = frame.resample("D").agg({"load": ["min", "max", "mean"], "ambient": ["min", "max", "mean"], "filled": "mean"})
    figure, axes = plt.subplots(2, 1, figsize=(11, 4.6), sharex=True)
    for axis, column, title, unit in ((axes[0], "load", "Load", "kVA"), (axes[1], "ambient", "Ambient", "°C")):
        for day in daily.index[daily[("filled", "mean")] > 0.5]:
            axis.axvspan(day, day + pd.Timedelta(days=1), color=colors["hairline"], alpha=0.5, linewidth=0, zorder=0)
        axis.fill_between(daily.index, daily[(column, "min")], daily[(column, "max")], color=colors["faint"], linewidth=0)
        axis.plot(daily.index, daily[(column, "mean")], color=colors["strong"], linewidth=1.6)
        axis.set_title(title)
        axis.set_ylabel(unit)
    axes[0].axhline(100, color=colors["ink"], linewidth=1.0, linestyle=(0, (4, 3)))
    style.legend(figure, [(colors["strong"], "Daily mean"), (colors["faint"], "Daily range"),
                          (colors["ink"], "Rating"), (colors["hairline"], "Filled")], colors)
    figure.tight_layout(h_pad=1.5)
    style.save(figure, directory, "inputs", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("reports/figures"))
