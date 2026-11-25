"""When each advisory is raised, on the learned health estimate."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.data.simulate import RUNS, STEPS_PER_DAY
from src.features.residuals import compute
from src.models import twin
from src.models.health import estimate
from src.monitoring.advisory import RULES, advise
from src.visualization import style

TITLES = {"cooling-summer": "Cooling, from Late Summer", "cooling-winter": "Cooling, from Winter",
          "losses-summer": "Extra Loss, from Late Summer", "losses-winter": "Extra Loss, from Winter"}
LABELS = {"cooling": "Rise factor", "losses": "No-load losses"}


def draw(theme: str, directory: Path) -> None:
    colors = style.apply(theme)
    unit = twin.load(Path("models/twin.json"))
    results = json.loads(Path("reports/results.json").read_text())["learned"]
    rules = {rule.cause: rule for rule in RULES}
    figure, axes = plt.subplots(2, 2, figsize=(11, 6.2))

    for axis, (run, title) in zip(axes.flat, TITLES.items()):
        fault, onset, growth = RUNS[run]
        frame = pd.read_parquet(f"data/{run}.parquet")
        health = estimate(compute(frame, unit))
        advice = advise(health)
        day = pd.Series(frame.index / STEPS_PER_DAY - onset, index=frame.index)
        window = (day > -20) & (day < growth + 5)
        rule = rules[fault]
        start = day[advice.index[advice[fault]][0]]
        axis.axvspan(start, day[window].max(), color=colors["faint"], linewidth=0, zorder=0)
        hourly = health.index[window][3::4]
        axis.plot(day[hourly], health.loc[hourly, rule.parameter], color=colors["strong"], linewidth=1.6)
        axis.axhline(rule.threshold, color=colors["ink"], linewidth=1.0, linestyle=(0, (4, 3)))
        axis.annotate(f"Advisory\n{results[run]['lead_days']:.0f} days before due", (start, 0.94),
                      xycoords=("data", "axes fraction"), xytext=(8, 0), textcoords="offset points",
                      va="top", fontsize=8, color=colors["ink"])
        axis.set_ylim(top=float(health.loc[hourly, rule.parameter].max()) * 1.12 if fault == "cooling" else 1.15)
        axis.set_title(title)
        axis.set_ylabel(LABELS[fault])
        axis.set_xlabel("Days from fault onset")
        axis.set_xlim(-20, growth + 5)

    style.legend(figure, [(colors["strong"], "Health, learned twin"), (colors["ink"], "Threshold"),
                          (colors["faint"], "Advisory raised")], colors)
    figure.tight_layout(w_pad=2.5, h_pad=2.0)
    style.save(figure, directory, "advisories", theme)


if __name__ == "__main__":
    for theme in ("light", "dark"):
        draw(theme, Path("reports/figures"))
