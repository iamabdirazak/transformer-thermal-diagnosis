"""The two faults, each a change to one physical parameter.

Severity runs from 0 (healthy) to 1 (due for maintenance).

    cooling   Radiators fouled, fins blocked or oil low: the tank sheds heat
              less well, so every degree of rise grows by the same factor,
              up to 40% at severity 1.
    losses    Heat made inside the tank that the load does not explain,
              as from a core fault or circulating currents: an extra loss up
              to one rated no-load loss at severity 1. It shows most at
              light load, where the normal losses are small.
"""

from dataclasses import replace

from src.plant.transformer import Transformer

FAULTS = ("cooling", "losses")
COOLING = 0.4  # rise grows by 40% at severity 1
LOSSES = 1.0  # extra loss, rated no-load losses at severity 1


def apply(unit: Transformer, fault: str | None, severity: float) -> Transformer:
    if fault is None or severity == 0:
        return unit
    if fault == "cooling":
        return replace(unit, rise_rated=unit.rise_rated * (1 + COOLING * severity))
    if fault == "losses":
        return replace(unit, extra_loss=unit.extra_loss + LOSSES * severity)
    raise ValueError(f"Unknown fault: {fault}")
