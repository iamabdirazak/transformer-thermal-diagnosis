import numpy as np

from src.plant.faults import apply
from src.plant.transformer import Transformer, ageing, top_oil


def test_oil_settles_at_ambient_plus_rated_rise():
    unit = Transformer()
    oil = top_oil(unit, np.ones(2000), np.full(2000, 30.0), start=30.0)
    assert abs(oil[-1] - (30.0 + unit.rise_rated)) < 1e-6


def test_ageing_is_one_at_98_and_doubles_every_6_kelvin():
    assert np.isclose(ageing(98.0), 1.0)
    assert np.isclose(ageing(104.0), 2.0)


def test_cooling_fault_scales_rise_at_every_load():
    unit = Transformer()
    faulty = apply(unit, "cooling", 1.0)
    for load in (0.2, 0.6, 1.0):
        assert np.isclose(faulty.rise(load) / unit.rise(load), 1.4)


def test_extra_loss_weighs_most_at_light_load():
    unit = Transformer()
    faulty = apply(unit, "losses", 1.0)
    assert faulty.rise(0.2) / unit.rise(0.2) > faulty.rise(1.0) / unit.rise(1.0)
