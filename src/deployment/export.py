"""Write one 15-minute step of the twin as an ONNX graph.

The graph takes the three readings and the twin's state, and returns the
next state and the terms the health estimate sums over its week. The
running sums and the advisory rules stay in the host loop: they are
state, a few additions per step, and need no graph.

Every operation is arithmetic, so the graph is written directly with
ONNX operators through a small expression builder.
"""

from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper, numpy_helper

from src.models import twin
from src.plant.transformer import RATING, STEP, Transformer

INPUTS = ("load", "ambient", "oil")
STATE = ("expected", "cooling_shape", "losses_shape")
TERMS = ("rc", "rl", "cc", "cl", "ll", "ageing", "hot_spot")


class Graph:
    def __init__(self):
        self.nodes, self.initializers, self.count = [], [], 0

    def name(self, prefix: str) -> str:
        self.count += 1
        return f"{prefix}_{self.count}"

    def constant(self, value, dtype=np.float32) -> "Expression":
        name = self.name("c")
        self.initializers.append(numpy_helper.from_array(np.array(value, dtype=dtype), name))
        return Expression(self, name)

    def op(self, kind: str, *inputs, **attributes) -> "Expression":
        output = self.name(kind.lower())
        self.nodes.append(helper.make_node(kind, [i.output for i in inputs], [output], **attributes))
        return Expression(self, output)

    def column(self, tensor: "Expression", i: int) -> "Expression":
        return self.op("Gather", tensor, self.constant(i, np.int64), axis=1)

    def stack(self, values: list["Expression"], name: str) -> None:
        columns = [self.op("Unsqueeze", v, self.constant([1], np.int64)) for v in values]
        self.nodes.append(helper.make_node("Concat", [c.output for c in columns], [name], axis=1))


class Expression:
    """A value in the graph. Arithmetic on it adds ONNX nodes."""

    def __init__(self, graph: Graph, output: str):
        self.graph, self.output = graph, output

    def wrap(self, other):
        return other if isinstance(other, Expression) else self.graph.constant(other)

    def __add__(self, other): return self.graph.op("Add", self, self.wrap(other))
    def __radd__(self, other): return self.graph.op("Add", self.wrap(other), self)
    def __sub__(self, other): return self.graph.op("Sub", self, self.wrap(other))
    def __rsub__(self, other): return self.graph.op("Sub", self.wrap(other), self)
    def __mul__(self, other): return self.graph.op("Mul", self, self.wrap(other))
    def __rmul__(self, other): return self.graph.op("Mul", self.wrap(other), self)
    def __truediv__(self, other): return self.graph.op("Div", self, self.wrap(other))
    def __pow__(self, exponent): return self.graph.op("Pow", self, self.wrap(exponent))
    def __rpow__(self, base): return self.graph.op("Pow", self.wrap(base), self)
    def at_least(self, floor: float): return self.graph.op("Max", self, self.wrap(floor))


def build(unit: Transformer) -> onnx.ModelProto:
    graph = Graph()
    readings, state = Expression(graph, "readings"), Expression(graph, "state")
    load_kva, ambient, oil = (graph.column(readings, i) for i in range(3))
    expected, cooling, losses = (graph.column(state, i) for i in range(3))

    # Plant physics and fault shapes, as in src/features/residuals.py
    load = (load_kva / RATING).at_least(0.0)
    base = (1 + unit.loss_ratio * load * load) / (1 + unit.loss_ratio)
    rise = unit.rise_rated * base ** unit.oil_exponent
    sensitivity = unit.rise_rated * unit.oil_exponent / (1 + unit.loss_ratio) * base ** (unit.oil_exponent - 1)
    gain = STEP / unit.oil_constant

    residual = oil - expected
    hot_spot = oil + unit.hot_spot_gradient * load ** unit.winding_exponent
    ageing = 2.0 ** ((hot_spot - 98.0) / 6.0)

    graph.stack([expected + gain * (ambient + rise - expected),
                 cooling + gain * (rise - cooling),
                 losses + gain * (sensitivity - losses)], "next_state")
    graph.stack([residual * cooling, residual * losses, cooling * cooling, cooling * losses, losses * losses,
                 ageing, hot_spot], "terms")

    model = helper.make_model(helper.make_graph(
        graph.nodes, "transformer_thermal_diagnosis",
        [helper.make_tensor_value_info("readings", TensorProto.FLOAT, ["units", len(INPUTS)]),
         helper.make_tensor_value_info("state", TensorProto.FLOAT, ["units", len(STATE)])],
        [helper.make_tensor_value_info("next_state", TensorProto.FLOAT, ["units", len(STATE)]),
         helper.make_tensor_value_info("terms", TensorProto.FLOAT, ["units", len(TERMS)])],
        graph.initializers,
    ), opset_imports=[helper.make_opsetid("", 17)], producer_name="transformer-thermal-diagnosis", ir_version=8)
    model.doc_string = "Load, ambient and top oil every 15 minutes in; next twin state and health terms out."
    onnx.checker.check_model(model)
    return model


def initial_state(unit: Transformer, load_kva: float, oil: float) -> np.ndarray:
    """The twin starts at the first oil reading, its shapes at their steady values."""
    from src.features.residuals import drivers
    rise, sensitivity = drivers(unit, load_kva / RATING)
    return np.array([[oil, rise, sensitivity]], dtype=np.float32)


if __name__ == "__main__":
    model = build(twin.load(Path("models/twin.json")))
    path = Path("models/transformer.onnx")
    onnx.save(model, path)
    print(f"{path}  {path.stat().st_size / 1024:.1f} KB  {len(model.graph.node)} operators")
