"""Fit the twin on the first six healthy weeks and report how well it holds.

Test error is measured on the rest of the healthy run, months the fit
never saw, from late summer into winter.
"""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.simulate import STEPS_PER_DAY, UNIT
from src.models import twin
from src.plant.transformer import RATING, Transformer, top_oil

TRAINING_DAYS = 42


def error(unit: Transformer, frame: pd.DataFrame) -> float:
    oil = top_oil(unit, frame["load"].to_numpy() / RATING, frame["ambient"].to_numpy(), start=frame["oil"].iloc[0])
    return float(np.sqrt(np.mean((oil - frame["oil"].to_numpy()) ** 2)))


if __name__ == "__main__":
    frame = pd.read_parquet("data/healthy.parquet")
    split = TRAINING_DAYS * STEPS_PER_DAY
    training, test = frame.iloc[:split], frame.iloc[split:]
    learned = twin.fit(training)
    Path("models").mkdir(exist_ok=True)
    twin.save(learned, Path("models/twin.json"))

    report = {
        "parameters": {name: {"standard": getattr(Transformer(), name), "learned": round(getattr(learned, name), 2),
                              "true": getattr(UNIT, name)} for name in twin.FITTED},
        "oil_rmse_test": {"standard": round(error(Transformer(), test), 2), "learned": round(error(learned, test), 2)},
        "training_days": TRAINING_DAYS,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/twin.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
