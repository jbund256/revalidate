# coding=utf-8
"""Public package interface for varman."""

import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from .typing import INVALID
from .classification import compute, getter, setter
from .variable import Variable, VariableManager
from .variable_prototype import variable
from .base import VariableBase
