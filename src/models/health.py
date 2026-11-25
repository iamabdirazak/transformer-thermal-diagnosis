"""Health in engineering units, solved from a week of residuals by least squares.

    residual ≈ (c − 1) · s_cooling + e · s_losses

A week holds every load the unit sees, weekdays and weekend, day and
night, so the two shapes separate and the estimate stops depending on
how hard the transformer happens to be working.

    cooling   rise factor c: 1.0 healthy, 1.2 means every degree of rise is 20% higher
    losses    extra internal loss e, in rated no-load losses: 0.0 healthy
    ageing    insulation life used per day of service, over the last day: 1.0 at a 98 °C hot spot
"""

import numpy as np
import pandas as pd

from src.plant.transformer import ageing

WINDOW = 7 * 96  # steps of 15 minutes
DAY = 96
PARAMETERS = ("cooling", "losses", "ageing")


def solve(sums: dict) -> tuple:
    """The 2×2 normal equations, from running sums."""
    a, b, d = sums["cc"], sums["cl"], sums["ll"]
    determinant = a * d - b * b
    return (d * sums["rc"] - b * sums["rl"]) / determinant, (a * sums["rl"] - b * sums["rc"]) / determinant


def estimate(residuals: pd.DataFrame) -> pd.DataFrame:
    r, c, l = residuals["residual"], residuals["cooling_shape"], residuals["losses_shape"]
    total = lambda values: values.rolling(WINDOW, min_periods=WINDOW).sum()
    sums = {"rc": total(r * c), "rl": total(r * l), "cc": total(c * c), "cl": total(c * l), "ll": total(l * l)}
    cooling, losses = solve(sums)
    return pd.DataFrame({
        "cooling": 1 + cooling,
        "losses": losses,
        "ageing": pd.Series(ageing(residuals["hot_spot"]), index=residuals.index).rolling(DAY, min_periods=DAY).mean(),
    })
