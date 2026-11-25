"""Check the ONNX graph against the Python pipeline, then time it on one CPU thread.

Equivalence: stepping the graph through every run must reproduce the
reference residual shapes and health. Timing: one step at a time, as
the site computer calls it, against a 50 ms budget.
"""

import json
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd

from src.data.simulate import RUNS
from src.deployment.export import INPUTS, initial_state
from src.features.residuals import compute
from src.models import twin
from src.models.health import WINDOW, estimate, solve

BUDGET_MS = 50.0


def session() -> ort.InferenceSession:
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    return ort.InferenceSession("models/transformer.onnx", options, providers=["CPUExecutionProvider"])


def replay(model, unit, frame: pd.DataFrame) -> np.ndarray:
    readings = frame[list(INPUTS)].to_numpy(np.float32)
    state = initial_state(unit, frame["load"].iloc[0], frame["oil"].iloc[0])
    terms = np.empty((len(frame), 7))
    for i, row in enumerate(readings):
        state, out = model.run(None, {"readings": row[None], "state": state})
        terms[i] = out[0]
    return terms


def main() -> None:
    model, unit = session(), twin.load(Path("models/twin.json"))
    worst = 0.0
    for name in RUNS:
        frame = pd.read_parquet(f"data/{name}.parquet")
        terms = pd.DataFrame(replay(model, unit, frame), columns=["rc", "rl", "cc", "cl", "ll", "ageing", "hot_spot"])
        sums = terms[["rc", "rl", "cc", "cl", "ll"]].rolling(WINDOW, min_periods=WINDOW).sum()
        cooling, losses = solve(sums)
        expected = estimate(compute(frame, unit))
        worst = max(worst, float((1 + cooling - expected["cooling"]).abs().max()),
                    float((losses - expected["losses"]).abs().max()))

    row = frame[list(INPUTS)].to_numpy(np.float32)[:1]
    state = initial_state(unit, frame["load"].iloc[0], frame["oil"].iloc[0])
    for _ in range(200):
        model.run(None, {"readings": row, "state": state})
    timings = []
    for _ in range(5000):
        start = time.perf_counter()
        model.run(None, {"readings": row, "state": state})
        timings.append((time.perf_counter() - start) * 1000)

    edge = {
        "size_kb": round(Path("models/transformer.onnx").stat().st_size / 1024, 1),
        "latency_ms_median": round(float(np.median(timings)), 3),
        "latency_ms_p99": round(float(np.percentile(timings, 99)), 3),
        "budget_ms": BUDGET_MS,
        "max_health_difference": float(f"{worst:.2e}"),
    }
    results = json.loads(Path("reports/results.json").read_text())
    results["edge"] = edge
    Path("reports/results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(edge, indent=2))


if __name__ == "__main__":
    main()
