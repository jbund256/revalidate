# coding=utf-8

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import ClassVar, Optional


class VariableFunctionType(Enum):
    COMPUTE = auto()
    SET = auto()
    GET = auto()


@dataclass(frozen=True, slots=True)
class VariableFunctionClassification:
    param_function_type: VariableFunctionType
    name: str
    attr_name: ClassVar[str] = field(default="__param_func_class", init=False)

    @classmethod
    def mark_compute(cls, obj, name):
        setattr(obj, cls.attr_name, cls(VariableFunctionType.COMPUTE, name))

    @classmethod
    def mark_set(cls, obj, name):
        setattr(obj, cls.attr_name, cls(VariableFunctionType.SET, name))

    @classmethod
    def mark_get(cls, obj, name):
        setattr(obj, cls.attr_name, cls(VariableFunctionType.GET, name))

    @classmethod
    def check(cls, obj) -> Optional['VariableFunctionClassification']:
        return getattr(obj, cls.attr_name, None)


def compute(name: str):
    def wrapper(func):
        VariableFunctionClassification.mark_compute(func, name)
        return func
    return wrapper


def getter(name: str):
    def wrapper(func):
        VariableFunctionClassification.mark_get(func, name)
        return func
    return wrapper


def setter(name: str):
    def wrapper(func):
        VariableFunctionClassification.mark_set(func, name)
        return func
    return wrapper
