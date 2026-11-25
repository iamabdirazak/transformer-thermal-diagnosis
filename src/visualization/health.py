"""Health through the summer fault runs: standard unit, learned twin, and truth."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.data.simulate import RUNS, STEPS_PER_DAY
from src.evaluation.score import TRUTH
from src.features.residuals import compute
from src.models import twin
from src.models.health import estimate
from src.plant.transformer import Transformer
from src.visualization import style

PANELS = {"cooling-summer": ("Rise Factor", "× healthy"), "losses-summer": ("Extra Internal Loss", "No-load losses")}


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    learned = twin.load(Path("models/twin.json"))
    figure, axes = plt.subplots(1, 2, figsize=(11, 3.6))
    for axis, (run, (title, unit)) in zip(axes, PANELS.items()):
        fault, onset, growth = RUNS[run]
        frame = pd.read_parquet(f"data/{run}.parquet")
        day = pd.Series(frame.index / STEPS_PER_DAY - onset, index=frame.index)
        hourly = frame.index[((day > -20) & (day < growth + 5)).to_numpy()][3::4]
        for model, shade in ((Transformer(), colors["soft"]), (learned, colors["strong"])):
            axis.plot(day[hourly], estimate(compute(frame, model)).loc[hourly, fault], color=shade, linewidth=1.6)
        axis.plot(day[hourly], TRUTH[fault](frame.loc[hourly, "severity"]), color=colors["ink"], linewidth=1.0,
                  linestyle=(0, (4, 3)))
        axis.set_title(title)
        axis.set_ylabel(unit)
        axis.set_xlabel("Days from fault onset")
        axis.set_xlim(-20, growth + 5)
    style.legend(figure, [(colors["soft"], "Standard unit"), (colors["strong"], "Learned twin"),
                          (colors["ink"], "True")], colors)
    figure.tight_layout(w_pad=2.5)
    style.save(figure, directory, "health", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("reports/figures"))
