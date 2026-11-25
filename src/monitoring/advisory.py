"""From health to advice: one rule per condition, in engineering units.

A rule raises its advisory when its parameter has crossed the threshold
for a full on-delay, and clears it only once the parameter is back past a
deadband. Thresholds are maintenance criteria, not statistics.
"""

from dataclasses import dataclass

import pandas as pd

STEPS_PER_HOUR = 4


@dataclass(frozen=True)
class Rule:
    cause: str
    parameter: str
    threshold: float
    clear: float  # the deadband edge the parameter must return past
    advice: str

    def exceeded(self, value: float) -> bool:
        return value > self.threshold

    def cleared(self, value: float) -> bool:
        return value < self.clear


RULES = (
    Rule("cooling", "cooling", 1.10, 1.06,
         "Cooling degraded: oil rise 10% above normal. Inspect radiators, oil level and fins."),
    Rule("losses", "losses", 0.25, 0.15,
         "Extra internal heat: a quarter of the no-load loss unexplained by load. Take an oil sample for gas analysis."),
    Rule("ageing", "ageing", 1.0, 0.8,
         "Accelerated ageing: insulation used faster than rated today. Shift or shed evening load."),
)

ON_DELAY = 6  # hours the threshold must stay crossed


class Latch:
    """One rule's state, updated once an hour."""

    def __init__(self, rule: Rule):
        self.rule, self.active, self.count = rule, False, 0

    def update(self, value: float) -> bool:
        if pd.isna(value):
            return self.active
        if self.active:
            self.active = not self.rule.cleared(value)
        else:
            self.count = self.count + 1 if self.rule.exceeded(value) else 0
            self.active = self.count >= ON_DELAY
        return self.active


def advise(health: pd.DataFrame) -> pd.DataFrame:
    """Hourly advisory state for each rule."""
    hourly = health.iloc[STEPS_PER_HOUR - 1::STEPS_PER_HOUR]
    states = {}
    for rule in RULES:
        latch = Latch(rule)
        states[rule.cause] = [latch.update(value) for value in hourly[rule.parameter]]
    return pd.DataFrame(states, index=hourly.index)
