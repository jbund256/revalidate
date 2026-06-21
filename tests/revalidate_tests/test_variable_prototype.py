# coding=utf-8
import inspect
from typing import Optional

import pytest

from revalidate import INVALID, Variable
from revalidate.variable_prototype import VariablePrototype
from revalidate.exceptions import VariableRenameError, VariableConsistencyError


def test_get_name():
    var_proto = VariablePrototype()
    var_proto.set_name("name")
    assert var_proto.get_name() == "name"


def test_name_cannot_be_reset():
    var_proto = VariablePrototype()
    var_proto.set_name("name")

    with pytest.raises(VariableRenameError):
        var_proto.set_name("new_name")


def test_has_compute_function():
    var_proto = VariablePrototype()
    assert not var_proto.has_compute_function()

    var_proto = VariablePrototype(compute_function=lambda x: 1)
    assert var_proto.has_compute_function()


def test_has_setter_function():
    var_proto = VariablePrototype()
    assert not var_proto.has_setter_function()

    var_proto = VariablePrototype(setter_function=lambda x: 1)
    assert var_proto.has_setter_function()


def test_has_getter_function():
    var_proto = VariablePrototype()
    assert not var_proto.has_getter_function()

    var_proto = VariablePrototype(getter_function=lambda x: 1)
    assert var_proto.has_getter_function()


def test_get_property():
    var_proto = VariablePrototype()

    prop = var_proto.get_property()
    assert isinstance(prop, property)
    assert var_proto.get_property() is prop


@pytest.mark.parametrize("read_only", [True, False])
@pytest.mark.parametrize("write_only", [True, False])
@pytest.mark.parametrize("doc", ["Documentation", None])
def test_property_1(read_only: bool, write_only: bool, doc: Optional[str]):
    """Test the retuned property object"""
    var_proto = VariablePrototype(default=1, read_only=read_only, write_only=write_only, doc=doc)
    prop = var_proto.get_property()

    if read_only:
        assert prop.fset is None
    else:
        assert prop.fset is not None
        assert callable(prop.fset)

    if write_only:
        assert prop.fget is None
    else:
        assert prop.fget is not None
        assert callable(prop.fget)

    assert prop.__doc__ == doc


@pytest.mark.parametrize("kwargs, has_default",
                         [({}, False),
                          ({"default": 4}, True),
                          ({"default_factory": lambda: 4}, True)])
def test_has_default(kwargs: dict, has_default: bool):
    """Test the has_default function"""
    var_proto = VariablePrototype(**kwargs)
    assert var_proto.has_default() == has_default


def test_multiple_defaults():
    with pytest.raises(VariableConsistencyError):
        vp = VariablePrototype(default=4, default_factory=lambda: 5)
        vp.build_variable()


@pytest.mark.parametrize("kwargs, default",
                         [({}, INVALID),
                          ({"default": 4}, 4),
                          ({"default_factory": lambda: 4}, 4)])
def test_get_default(kwargs, default):
    var_proto = VariablePrototype(**kwargs)

    assert var_proto.get_default() == default


def test_build_variable():
    var_proto = VariablePrototype()

    var = var_proto.build_variable()
    assert isinstance(var, Variable)
    assert var.prototype is var_proto


class CheckerVariablePrototype(VariablePrototype):

    def getter_func(self):
        return self._getter_func()

    def setter_func(self):
        return self._setter_func()


def test_getter_func():
    var_proto = CheckerVariablePrototype()

    getter_func = var_proto.getter_func()

    assert callable(getter_func)

    signature = inspect.signature(getter_func)
    assert len(signature.parameters) == 1


def test_setter_func():
    var_proto = CheckerVariablePrototype()

    setter_func = var_proto.setter_func()

    assert callable(setter_func)

    signature = inspect.signature(setter_func)
    assert len(signature.parameters) == 2
    assert signature.return_annotation is None
