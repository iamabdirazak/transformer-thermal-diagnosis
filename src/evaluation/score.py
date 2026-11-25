"""Score the advisories the way an operator would.

    lead time          days between the advisory and the fault reaching
                       maintenance severity
    true health        what the parameter really was when the advisory came
    false advisories   fault advisories on healthy data, per month
    ageing             advisory hours against hours the true ageing rate
                       was above 1

The first six weeks of every run are the twin's training period and are
not scored. The learned twin and the standard's typical unit are scored
side by side.
"""

import json
from pathlib import Path

import pandas as pd

from src.data.simulate import RUNS, STEPS_PER_DAY
from src.features.residuals import compute
from src.models import twin
from src.models.health import DAY, estimate
from src.models.train import TRAINING_DAYS
from src.monitoring.advisory import advise
from src.plant.faults import COOLING, LOSSES
from src.plant.transformer import Transformer

TRUTH = {"cooling": lambda s: 1 + COOLING * s, "losses": lambda s: LOSSES * s}
HOURS_PER_MONTH = 30 * 24


def run(name: str, unit: Transformer):
    frame = pd.read_parquet(f"data/{name}.parquet")
    advice = advise(estimate(compute(frame, unit)))
    return frame, advice.loc[advice.index >= TRAINING_DAYS * STEPS_PER_DAY]


def score(unit: Transformer) -> dict:
    result = {}
    for name, (fault, _, _) in RUNS.items():
        if fault is None:
            continue
        frame, advice = run(name, unit)
        raised = advice.index[advice[fault]]
        healthy = advice.index[frame.loc[advice.index, "severity"] == 0]
        entry = {"other_causes_raised": [c for c in ("cooling", "losses") if c != fault and advice[c].any()],
                 "false_hours_before_onset": int(advice.loc[healthy, fault].sum())}
        if len(raised):
            first = raised[0]
            due = frame.index[frame["severity"] >= 1][0]
            severity = float(frame["severity"].iloc[first])
            entry.update({"lead_days": round((due - first) / STEPS_PER_DAY, 1),
                          "severity": round(severity, 2), "true_health": round(TRUTH[fault](severity), 3)})
        else:
            entry["lead_days"] = None
        result[name] = entry

    frame, advice = run("healthy", unit)
    onsets = (advice[["cooling", "losses"]] & ~advice[["cooling", "losses"]].shift(fill_value=False)).sum().sum()
    months = len(advice) / HOURS_PER_MONTH
    true_daily = frame["true_ageing"].rolling(DAY, min_periods=DAY).mean().loc[advice.index]
    result["healthy"] = {
        "months": round(months, 2),
        "false_advisories_per_month": round(int(onsets) / months, 2),
        "ageing_hours_true": int((true_daily > 1).sum()),
        "ageing_hours_advised": int(advice["ageing"].sum()),
        "ageing_hours_agreeing": int((advice["ageing"] & (true_daily > 1)).sum()),
    }
    return result


if __name__ == "__main__":
    results = {"learned": score(twin.load(Path("models/twin.json"))), "standard": score(Transformer())}
    Path("reports/results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
