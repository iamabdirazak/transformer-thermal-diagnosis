"""The learned twin: this unit's own thermal parameters, read from its oil gauge.

A new transformer arrives with a test report at best, and its rise, loss
ratio and oil time constant drift from the standard's typical values.
The twin starts from IEC 60076-7's ONAN defaults and fits three of them
to the first weeks of healthy data, by least squares on the measured top
oil, through the same difference equation the plant obeys:

    rise_rated     Δθ_or, top-oil rise at rated load
    loss_ratio     R, load losses over no-load losses
    oil_constant   τ_o, how fast the oil follows

The oil exponent and the hot-spot gradient stay at the standard's
values: top-oil data alone cannot separate them from the three above.
"""

import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from src.plant.transformer import RATING, Transformer, top_oil

FITTED = ("rise_rated", "loss_ratio", "oil_constant")
BOUNDS = ([20.0, 1.0, 30.0], [90.0, 15.0, 600.0])


def fit(frame: pd.DataFrame, start: Transformer = Transformer()) -> Transformer:
    load = frame["load"].to_numpy() / RATING
    ambient, oil = frame["ambient"].to_numpy(), frame["oil"].to_numpy()

    def error(values):
        unit = replace(start, **dict(zip(FITTED, values)))
        return top_oil(unit, load, ambient, start=oil[0]) - oil

    solution = least_squares(error, [getattr(start, name) for name in FITTED], bounds=BOUNDS, x_scale="jac")
    return replace(start, **dict(zip(FITTED, solution.x)))


def save(unit: Transformer, path: Path) -> None:
    path.write_text(json.dumps(asdict(unit), indent=2))


def load(path: Path) -> Transformer:
    return Transformer(**json.loads(path.read_text()))
