# coding=utf-8
"""Public package interface for varman."""

import logging

from .base import VariableBase
from .classification import compute, getter, setter
from .typing import INVALID
from .variable import Variable, VariableManager
from .variable_prototype import variable

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["INVALID", "compute", "getter", "setter", "Variable", "VariableManager", "variable", "VariableBase"]
