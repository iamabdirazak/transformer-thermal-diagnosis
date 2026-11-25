"""What the monitor reads, every 15 minutes.

The oil gauge reports whole degrees, as the field monitor does, after a
little noise. Load comes from the power meter. Ambient is the field
monitor's own reading, which is also what drove the plant.
"""

import numpy as np

OIL_NOISE = 0.3  # °C, one standard deviation, before rounding
LOAD_NOISE = 0.5  # kVA


def read(oil: np.ndarray, load: np.ndarray, ambient: np.ndarray, rng: np.random.Generator) -> dict[str, np.ndarray]:
    return {
        "load": load + rng.normal(0, LOAD_NOISE, len(load)),
        "ambient": ambient,
        "oil": np.round(oil + rng.normal(0, OIL_NOISE, len(oil))),
    }
