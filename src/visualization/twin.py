"""The learned twin against the standard's typical unit, on a winter week it never saw."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.features.residuals import compute
from src.models import twin
from src.plant.transformer import Transformer
from src.visualization import style

WEEK = ("2020-01-20", "2020-01-27")


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    frame = pd.read_parquet("data/healthy.parquet")
    learned, standard = compute(frame, twin.load(Path("models/twin.json"))), compute(frame, Transformer())
    frame = frame.assign(learned=frame["oil"] - learned["residual"], standard=frame["oil"] - standard["residual"])
    frame = frame.set_index("time").loc[WEEK[0]:WEEK[1]]
    figure, axis = plt.subplots(figsize=(11, 3.4))
    axis.plot(frame.index, frame["oil"], color=colors["hairline"] if theme == "light" else colors["secondary"],
              linewidth=1.2, drawstyle="steps-post")
    axis.plot(frame.index, frame["standard"], color=colors["soft"], linewidth=1.6)
    axis.plot(frame.index, frame["learned"], color=colors["strong"], linewidth=1.6)
    axis.set_title("Top Oil")
    axis.set_ylabel("°C")
    style.legend(figure, [(colors["hairline"] if theme == "light" else colors["secondary"], "Measured"),
                          (colors["soft"], "Standard unit"), (colors["strong"], "Learned twin")], colors)
    figure.tight_layout()
    style.save(figure, directory, "twin", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("reports/figures"))
