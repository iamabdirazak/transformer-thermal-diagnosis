import json
from pathlib import Path

import pandas as pd

from src.data.simulate import UNIT
from src.features.residuals import compute
from src.models import twin
from src.models.health import estimate
from src.monitoring.monitor import Monitor


def test_twin_recovers_the_unit():
    learned = twin.load(Path("models/twin.json"))
    for name in twin.FITTED:
        assert abs(getattr(learned, name) / getattr(UNIT, name) - 1) < 0.02


def test_healthy_run_stays_inside_the_deadbands():
    frame = pd.read_parquet("data/healthy.parquet")
    health = estimate(compute(frame, twin.load(Path("models/twin.json")))).dropna()
    assert health["cooling"].between(0.97, 1.03).all()
    assert health["losses"].abs().max() < 0.1


def test_every_fault_is_caught_early_and_named_right():
    results = json.loads(Path("reports/results.json").read_text())["learned"]
    for name, entry in results.items():
        if name == "healthy":
            assert entry["false_advisories_per_month"] == 0
            continue
        assert entry["lead_days"] > 30
        assert entry["other_causes_raised"] == []


def test_edge_graph_matches_and_fits_the_budget():
    edge = json.loads(Path("reports/results.json").read_text())["edge"]
    assert edge["max_health_difference"] < 1e-4
    assert edge["latency_ms_p99"] < edge["budget_ms"]


def test_monitor_raises_cooling_advisory_on_a_faulty_run():
    frame = pd.read_parquet("data/cooling-summer.parquet")
    monitor, raised = Monitor(), set()
    for row in frame[["load", "ambient", "oil"]].to_dict("records"):
        monitor.step(row)
        raised.update(monitor.advisories)
    assert any(advice.startswith("Cooling degraded") for advice in raised)
    assert not any(advice.startswith("Extra internal heat") for advice in raised)
