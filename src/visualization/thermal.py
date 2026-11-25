"""One summer week of the healthy run: ambient, top oil and the hot spot it implies."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.features.residuals import compute
from src.models import twin
from src.visualization import style

WEEK = ("2019-08-12", "2019-08-19")


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    frame = pd.read_parquet("data/healthy.parquet")
    hot = compute(frame, twin.load(Path("models/twin.json")))["hot_spot"]
    frame = frame.assign(hot_spot=hot).set_index("time").loc[WEEK[0]:WEEK[1]]
    figure, axes = plt.subplots(2, 1, figsize=(11, 4.8), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
    axis = axes[0]
    axis.plot(frame.index, frame["hot_spot"], color=colors["strong"], linewidth=1.6)
    axis.plot(frame.index, frame["oil"], color=colors["base"], linewidth=1.4, drawstyle="steps-post")
    axis.plot(frame.index, frame["ambient"], color=colors["secondary"], linewidth=1.2)
    axis.axhline(98, color=colors["ink"], linewidth=1.0, linestyle=(0, (4, 3)))
    axis.set_title("Temperatures")
    axis.set_ylabel("°C")
    axes[1].fill_between(frame.index, frame["load"], color=colors["faint"], linewidth=0)
    axes[1].plot(frame.index, frame["load"], color=colors["strong"], linewidth=1.0)
    axes[1].axhline(100, color=colors["ink"], linewidth=1.0, linestyle=(0, (4, 3)))
    axes[1].set_title("Load")
    axes[1].set_ylabel("kVA")
    style.legend(figure, [(colors["strong"], "Hot spot"), (colors["base"], "Top oil, measured"),
                          (colors["secondary"], "Ambient"), (colors["ink"], "98 °C, rated ageing")], colors)
    figure.tight_layout(h_pad=1.5)
    style.save(figure, directory, "thermal", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("reports/figures"))
