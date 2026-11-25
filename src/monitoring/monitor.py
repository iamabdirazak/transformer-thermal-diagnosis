"""The loop that runs on site: one call every 15 minutes.

The ONNX graph advances the twin and returns this step's terms. The
monitor keeps a week of terms as running sums, turns them into health,
and updates the advisory rules once an hour.
"""

from collections import deque
from pathlib import Path

import numpy as np
import onnxruntime as ort

from src.deployment.export import INPUTS, TERMS, initial_state
from src.models import twin
from src.models.health import DAY, WINDOW, solve
from src.monitoring.advisory import RULES, STEPS_PER_HOUR, Latch

SUMMED = TERMS[:5]


class Monitor:
    def __init__(self, model: Path = Path("models/transformer.onnx"), unit: Path = Path("models/twin.json")):
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(model), options, providers=["CPUExecutionProvider"])
        self.unit = twin.load(unit)
        self.state = None
        self.week, self.day = deque(maxlen=WINDOW), deque(maxlen=DAY)
        self.sums = np.zeros(len(SUMMED))
        self.latches = [Latch(rule) for rule in RULES]
        self.steps = 0
        self.health: dict[str, float] = {}
        self.advisories: list[str] = []

    def step(self, readings: dict[str, float]) -> None:
        """Take one 15-minute reading: load in kVA, ambient and top oil in °C."""
        row = np.array([[readings[name] for name in INPUTS]], dtype=np.float32)
        if self.state is None:
            self.state = initial_state(self.unit, readings["load"], readings["oil"])
        self.state, terms = self.session.run(None, {"readings": row, "state": self.state})
        summed, ageing = terms[0, :5].astype(float), float(terms[0, 5])
        if len(self.week) == WINDOW:
            self.sums -= self.week[0]
        self.week.append(summed)
        self.sums += summed
        self.day.append(ageing)
        self.steps += 1

        if len(self.week) == WINDOW:
            cooling, losses = solve(dict(zip(SUMMED, self.sums)))
            self.health = {"cooling": 1 + cooling, "losses": losses, "ageing": float(np.mean(self.day))}
            if self.steps % STEPS_PER_HOUR == 0:
                self.advisories = [latch.rule.advice for latch in self.latches
                                   if latch.update(self.health[latch.rule.parameter])]
