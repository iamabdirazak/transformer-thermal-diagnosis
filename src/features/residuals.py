"""Residual: measured top oil minus what the learned twin expects.

The twin runs alongside the transformer on the same load and ambient. A
healthy unit leaves only gauge noise. Each fault leaves its own shape,
and both shapes come from the equations:

    cooling   the rise grows by a factor c, so the residual is (c − 1)
              times the twin's own rise, filtered by the oil:
                  s_cooling = filter(Δθ_o,ss)
    losses    an extra loss e enters beside R·K², so to first order the
              residual is e times the rise's sensitivity to it, filtered:
                  s_losses = filter(∂Δθ_o,ss/∂e)

The filter is the oil's own first-order response. Cooling scales with
load; extra losses weigh most at light load. Over a week, those two
shapes are told apart by how they move with the load.
"""

import numpy as np
import pandas as pd

from src.plant.transformer import RATING, STEP, Transformer

SIGNALS = ("residual", "cooling_shape", "losses_shape", "hot_spot")


def drivers(unit: Transformer, load):
    """Steady rise and its sensitivity to an extra loss, at load factor K."""
    base = (1 + unit.loss_ratio * np.maximum(load, 0.0) ** 2) / (1 + unit.loss_ratio)
    rise = unit.rise_rated * base ** unit.oil_exponent
    sensitivity = unit.rise_rated * unit.oil_exponent * base ** (unit.oil_exponent - 1) / (1 + unit.loss_ratio)
    return rise, sensitivity


def compute(frame: pd.DataFrame, unit: Transformer) -> pd.DataFrame:
    load = frame["load"].to_numpy() / RATING
    ambient, oil = frame["ambient"].to_numpy(), frame["oil"].to_numpy()
    rise, sensitivity = drivers(unit, load)
    gain = STEP / unit.oil_constant

    expected = np.empty(len(frame))
    cooling, losses = np.empty(len(frame)), np.empty(len(frame))
    expected[0], cooling[0], losses[0] = oil[0], rise[0], sensitivity[0]
    for i in range(1, len(frame)):
        expected[i] = expected[i - 1] + gain * (ambient[i - 1] + rise[i - 1] - expected[i - 1])
        cooling[i] = cooling[i - 1] + gain * (rise[i - 1] - cooling[i - 1])
        losses[i] = losses[i - 1] + gain * (sensitivity[i - 1] - losses[i - 1])

    return pd.DataFrame({
        "residual": oil - expected,
        "cooling_shape": cooling,
        "losses_shape": losses,
        "hot_spot": unit.hot_spot(oil, load),
    }, index=frame.index)
