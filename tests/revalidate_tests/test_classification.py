# coding=utf-8

import pytest

from revalidate.classification import VariableFunctionClassification, VariableFunctionType, compute, getter, setter


def test_variable_function_type_contains_expected_members():
    assert {member.name for member in VariableFunctionType} == {"COMPUTE", "SET", "GET"}


def test_check_returns_none_for_unmarked_object():
    def plain_function():
        return None

    assert VariableFunctionClassification.check(plain_function) is None


@pytest.mark.parametrize("mark_method, expected_type",
                         [(VariableFunctionClassification.mark_compute, VariableFunctionType.COMPUTE),
                          (VariableFunctionClassification.mark_set, VariableFunctionType.SET),
                          (VariableFunctionClassification.mark_get, VariableFunctionType.GET), ], )
def test_mark_methods_attach_expected_classification(mark_method, expected_type):
    def fn() -> None:
        return None

    mark_method(fn, "radius")

    classification = VariableFunctionClassification.check(fn)
    assert classification is not None
    assert classification.param_function_type is expected_type
    assert classification.name == "radius"


def test_mark_overwrites_previous_classification():
    def fn() -> None:
        return None

    VariableFunctionClassification.mark_compute(fn, "radius")
    VariableFunctionClassification.mark_set(fn, "diameter")

    classification = VariableFunctionClassification.check(fn)
    assert classification is not None
    assert classification.param_function_type is VariableFunctionType.SET
    assert classification.name == "diameter"


@pytest.mark.parametrize("decorator_factory, expected_type",
                         [(compute, VariableFunctionType.COMPUTE),
                          (setter, VariableFunctionType.SET),
                          (getter, VariableFunctionType.GET),])
def test_decorators_return_same_function_and_attach_classification(decorator_factory, expected_type):
    def fn() -> None:
        return None

    decorated = decorator_factory("diameter")(fn)

    assert decorated is fn
    classification = VariableFunctionClassification.check(fn)
    assert classification is not None
    assert classification.param_function_type is expected_type
    assert classification.name == "diameter"
