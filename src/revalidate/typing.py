# coding=utf-8
"""Typing information"""

from typing import Callable, TypeVar

""" Example with the types:

class Circle(VariableBase):
    radius: float = variable()
    diameter: float = variable()

Then, C would be Circle and V would be float. The functions for the radius would be:

def compute_func(circle: Circle) -> float:
    return circle.diameter / 2

def setter_func(circle: Circle, radius: float) -> float:
    if radius <= 0:
        raise ValueError
    return radius

def getter_func(circle: Circle, radius: float) -> float:
    circle._num_get_radius += 1
    return radius
"""
C = TypeVar('C')  # The class that inherits from Parameter
V = TypeVar('V')  # The type of the variable

ComputeFunc = Callable[[C], V]
SetterFunc = Callable[[C, V], V]
GetterFunc = Callable[[C, V], V]


class _InvalidType:

    def __repr__(self):
        return "INVALID"


INVALID = _InvalidType()
