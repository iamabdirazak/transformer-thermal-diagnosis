"""The thermal plant: IEC 60076-7 for an oil-immersed distribution transformer.

Losses heat the oil, the radiators cool it to ambient. Load losses grow
with the square of the load factor K, no-load losses do not, so the
top-oil rise the transformer heads for is

    Δθ_o,ss = Δθ_or · [(1 + R·K²) / (1 + R)]^x

and the oil approaches it with the oil time constant τ_o:

    τ_o · dθ_o/dt = θ_a + Δθ_o,ss − θ_o

The winding hot spot sits a further H·g_r·K^y above the top oil. Its own
time constant is a few minutes, so at 15-minute steps it is taken as
settled. Paper insulation ages at a rate that doubles every 6 K above
98 °C:

    V = 2^((θ_h − 98) / 6)

The defaults are IEC 60076-7's values for ONAN distribution transformers.
"""

from dataclasses import dataclass

import numpy as np

STEP = 15.0  # minutes
RATING = 100.0  # kVA, 11/0.433 kV, ONAN


@dataclass(frozen=True)
class Transformer:
    rise_rated: float = 55.0  # Δθ_or, K, top-oil rise at rated load
    loss_ratio: float = 5.0  # R, load losses / no-load losses at rated load
    oil_exponent: float = 0.8  # x
    oil_constant: float = 180.0  # τ_o, minutes
    hot_spot_gradient: float = 1.1 * 23.0  # H·g_r, K, hot spot above top oil at rated load
    winding_exponent: float = 1.6  # y
    extra_loss: float = 0.0  # added heat inside the tank, in units of rated no-load loss

    def rise(self, load) -> np.ndarray:
        """Steady top-oil rise over ambient for a load factor K."""
        k2 = np.maximum(load, 0.0) ** 2
        return self.rise_rated * ((1 + self.loss_ratio * k2 + self.extra_loss) / (1 + self.loss_ratio)) ** self.oil_exponent

    def hot_spot(self, top_oil, load) -> np.ndarray:
        return top_oil + self.hot_spot_gradient * np.maximum(load, 0.0) ** self.winding_exponent


def top_oil(unit: Transformer, load: np.ndarray, ambient: np.ndarray, start: float | None = None) -> np.ndarray:
    """Top-oil temperature at each step, by the IEC difference equation."""
    gain = STEP / unit.oil_constant
    target = ambient + unit.rise(load)
    oil = np.empty(len(load))
    oil[0] = target[0] if start is None else start
    for i in range(1, len(load)):
        oil[i] = oil[i - 1] + gain * (target[i - 1] - oil[i - 1])
    return oil


def ageing(hot_spot) -> np.ndarray:
    """Relative ageing rate of non-upgraded paper: 1.0 at a 98 °C hot spot."""
    return 2.0 ** ((np.asarray(hot_spot) - 98.0) / 6.0)
