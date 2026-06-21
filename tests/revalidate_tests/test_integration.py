# coding=utf-8

import numpy as np
import pytest

from revalidate import INVALID, VariableBase, compute, getter, setter, variable
from revalidate.exceptions import VariableComputationError


class Circle(VariableBase):
    radius = variable(depends_on=["diameter", "area", "circumference"])
    diameter = variable(depends_on=["radius"])
    area = variable(depends_on=["radius"])
    circumference = variable(depends_on=["radius"], doc="The circumference of the circle")

    def __init__(self, radius):
        super().__init__()
        self.radius = radius

    @compute("diameter")
    def _compute_diameter(self):
        return 2 * self.radius

    @compute("radius")
    def _compute_radius(self):
        if self._variable_manager.diameter.valid:
            return self.diameter / 2
        if self._variable_manager.circumference.valid:
            return self.circumference / 2 / np.pi
        if self._variable_manager.area.valid:
            return np.sqrt(self.area / np.pi)
        return INVALID

    @compute("area")
    def _compute_area(self):
        return self.radius ** 2 * np.pi

    @compute("circumference")
    def _compute_circumference(self):
        return 2 * self.radius * np.pi


def test_circle_1():
    c = Circle(1)

    assert c.radius == 1
    assert c.diameter == 2
    assert np.isclose(c.area, np.pi)
    assert np.isclose(c.circumference, 2 * np.pi)

    c.radius = 2
    assert c.radius == 2
    assert c.diameter == 4
    assert np.isclose(c.area, 4 * np.pi)
    assert np.isclose(c.circumference, 4 * np.pi)

    c.diameter = 2
    assert c.radius == 1
    assert c.diameter == 2
    assert np.isclose(c.area, np.pi)
    assert np.isclose(c.circumference, 2 * np.pi)

    c.area = 9 * np.pi
    assert c.radius == 3
    assert c.diameter == 6
    assert np.isclose(c.area, 9 * np.pi)
    assert np.isclose(c.circumference, 6 * np.pi)

    c.circumference = 4 * np.pi
    assert c.radius == 2
    assert c.diameter == 4
    assert np.isclose(c.area, 4 * np.pi)
    assert np.isclose(c.circumference, 4 * np.pi)


def test_circle_2():
    c_1 = Circle(1)
    c_2 = Circle(2)

    assert c_1.radius == 1
    assert c_1.diameter == 2
    assert np.isclose(c_1.area, np.pi)
    assert np.isclose(c_1.circumference, 2 * np.pi)

    assert c_2.radius == 2
    assert c_2.diameter == 4
    assert np.isclose(c_2.area, 4 * np.pi)
    assert np.isclose(c_2.circumference, 4 * np.pi)


class VariableClassReadOnly(VariableBase):
    a = variable(read_only=True, depends_on=["b"])
    b = variable(default=2)

    @compute("a")
    def compute_a(self):
        return self.b + 1


def test_read_only():
    mv = VariableClassReadOnly()
    assert mv.a == 3
    with pytest.raises(AttributeError):
        mv.a = 4

    mv.b = 4
    assert mv.a == 5


class VariableClassWriteOnly(VariableBase):
    a = variable(write_only=True, default=1)
    b = variable(depends_on=["a"])

    @compute("b")
    def compute_b(self):
        return self._variable_manager["a"].value + 1


def test_write_only():
    mv = VariableClassWriteOnly()
    mv.a = 4
    with pytest.raises(AttributeError):
        _ = mv.a

    assert mv.b == 5


class VariableClassInvalid(VariableBase):
    a = variable()
    b = variable(use_invalid_value=True)
    c = variable(use_invalid_value=True, invalid_value=5)
    d = variable(use_invalid_value=True)
    e = variable(use_invalid_value=False)

    @compute("d")
    def _compute_d(self):
        raise ValueError

    @compute("e")
    def _compute_e(self):
        raise ValueError


def test_invalid_value():
    v = VariableClassInvalid()

    with pytest.raises(VariableComputationError):
        _ = v.a

    assert v.b == INVALID
    assert v.c == 5
    assert v.d == INVALID
    v.d = 3
    assert v.d == 3

    with pytest.raises(VariableComputationError):
        _ = v.e


class VariableClassGetterFunc(VariableBase):
    a = variable()
    b = variable(use_invalid_value=True)

    def __init__(self):
        self.number_get_a = 0
        self.number_get_b = 0

    @getter("a")
    def _getter_a(self, a):
        self.number_get_a += 1
        return a

    @getter("b")
    def _getter_b(self, b):
        self.number_get_b += 1
        return b


def test_getter_func():
    v = VariableClassGetterFunc()

    with pytest.raises(VariableComputationError):
        _ = v.a
    assert v.number_get_a == 0

    v.a = 3
    assert v.a == 3
    assert v.number_get_a == 1

    assert v.b == INVALID
    assert v.number_get_b == 1

    v.b = 4
    assert v.b == 4
    assert v.number_get_b == 2


class VariableClassComputeFunc(VariableBase):
    a = variable()

    def __init__(self):
        self.number_compute_a = 0

    @compute("a")
    def _compute_a(self):
        self.number_compute_a += 1
        return 1


def test_compute_func():
    v = VariableClassComputeFunc()

    assert v.number_compute_a == 0
    _ = v.a
    assert v.number_compute_a == 1
    v.a = 3
    assert v.a == 3
    assert v.number_compute_a == 1


class VariableClassSetterFunc(VariableBase):
    a = variable()
    b = variable(depends_on=["a"], use_invalid_value=True, default=1)

    def __init__(self):
        self.set_a = 0

    @compute("a")
    def _compute_a(self):
        return 3

    @setter("a")
    def _setter_a(self, a):
        self.set_a += 1
        return a


def test_setter_func_1():
    v = VariableClassSetterFunc()

    assert v.set_a == 0
    _ = v.a
    assert v.set_a == 0
    v.a = 1
    assert v.a == 1
    assert v.set_a == 1


def test_setter_func_2():
    v = VariableClassSetterFunc()

    assert v.b == 1
    assert v.set_a == 0
    _ = v.a
    assert v.b == 1
    assert v.set_a == 0
    v.a = 1
    assert v.a == 1
    assert v.set_a == 1
    assert v.b == INVALID


class Settings(VariableBase):
    consistent: bool = variable(depends_on=["a", "b", "c"])
    a = variable()
    b = variable()
    c = variable()

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c
        self.number_computed_consistency = 0

    @compute("consistent")
    def _check_consistency(self):
        self.number_computed_consistency += 1

        if self.a + self.b + self.c > 10:
            return False
        return True


def test_settings():
    s = Settings(1, 2, 3)

    assert s.number_computed_consistency == 0
    assert s.consistent
    assert s.number_computed_consistency == 1
    assert s.consistent
    assert s.number_computed_consistency == 1

    s.a = 2
    assert s.number_computed_consistency == 1
    assert s.consistent
    assert s.number_computed_consistency == 2
    assert s.consistent
    assert s.number_computed_consistency == 2

    s.a = 10
    assert s.number_computed_consistency == 2
    assert not s.consistent
    assert s.number_computed_consistency == 3
    assert not s.consistent
    assert s.number_computed_consistency == 3


class System(VariableBase):
    input_1: float = variable()
    input_2: float = variable()

    output_1 = variable(depends_on=["input_1", "input_2"], read_only=True)
    output_2 = variable(depends_on=["input_2"], read_only=True)
    output_3 = variable(depends_on=["output_1"], read_only=True)

    def __init__(self, input_1, input_2):
        self.input_1 = input_1
        self.input_2 = input_2

    @compute("output_1")
    def _compute_output_1(self):
        return self.input_1 + self.input_2

    @compute("output_2")
    def _compute_2(self):
        return 2 * self.input_2

    @compute("output_3")
    def _compute_3(self):
        return 2 * self.output_1

    def all_values(self):
        return self.input_1, self.input_2, self.output_1, self.output_2, self.output_3


def test_system():
    in_1, in_2 = 1, 2
    system = System(in_1, in_2)
    assert system.all_values() == (in_1, in_2, in_1 + in_2, 2 * in_2, 2 * (in_1 + in_2))

    system.input_1 = in_1 = 2
    assert system.all_values() == (in_1, in_2, in_1 + in_2, 2 * in_2, 2 * (in_1 + in_2))

    system.input_2 = in_2 = 3
    assert system.all_values() == (in_1, in_2, in_1 + in_2, 2 * in_2, 2 * (in_1 + in_2))


