# coding=utf-8
"""The prototype classes"""
import inspect
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional

from .classification import VariableFunctionClassification, VariableFunctionType
from .constants import VARIABLE_MANAGER_NAME
from .exceptions import (
    VariableComputationError,
    VariableConsistencyError,
    VariableInitError,
    VariableNotFoundError,
    VariableRenameError,
)
from .typing import INVALID, C, ComputeFunc, GetterFunc, SetterFunc, V
from .utils import UniqueDict
from .variable import Variable, VariableManager

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class VariablePrototype(Generic[C, V]):
    compute_function: Optional[ComputeFunc] = field(default=None)
    setter_function: Optional[SetterFunc] = field(default=None)
    getter_function: Optional[GetterFunc] = field(default=None)
    depends_on: tuple[str] = field(default_factory=tuple)
    invalidates: tuple[str] = field(default_factory=tuple)
    default: Optional[V] = field(default=None)
    default_factory: Optional[Callable[[], V]] = field(default=None)
    read_only: bool = field(default=False)
    write_only: bool = field(default=False)
    #: Value used in the return when a value is invalid and cannot be computed (yet)
    invalid_value: Any = field(default=INVALID)
    #: Whether to use the invalid value or not.  If not, an exception is raised when a value is requested but could not
    #: be obtained
    use_invalid_value: bool = field(default=False)
    doc: Optional[str] = field(default=None)

    __name: Optional[str] = field(default=None, init=False)
    __property: Optional[property] = field(default=None, init=False)
    internal_default: Any = field(default=INVALID, init=False)

    def _check_default(self) -> list[str]:
        errors = []
        if self.default is not None and self.default_factory is not None:
            errors.append("A default and a default factory is defined on the variable prototype.")
        return errors

    def _check_read_only(self):
        """When a variable is read-only, it either needs a default or needs to be computable"""
        errors = []
        if not self.read_only:
            return errors
        if not self.has_default() and self.compute_function is None:
            errors.append("A read-only variable needs a default or a compute function")
        return errors

    def _check_not_read_and_write_only(self):
        errors = []
        if self.read_only and self.write_only:
            errors.append("Variable cannot be read only and write only.")
        return errors

    def consistency_check(self):
        errors = []

        errors.extend(self._check_default())
        errors.extend(self._check_read_only())
        errors.extend(self._check_not_read_and_write_only())

        if errors:
            raise VariableConsistencyError(errors)

    def set_name(self, name):
        if self.__name is not None:
            raise VariableRenameError(self.__name, name)
        self.__name = name

    def get_name(self) -> str:
        return self.__name

    def has_compute_function(self):
        return self.compute_function is not None

    def has_getter_function(self):
        return self.getter_function is not None

    def has_setter_function(self):
        return self.setter_function is not None

    # @property
    # def internal_name(self) -> str:
    #     """The name of the internal variable that holds the variables value and that is saved on the object"""
    #     return "_var_" + self.__name

    def get_property(self) -> property:
        if self.__property is None:
            fset = self._setter_func() if not self.read_only else None
            fget = self._getter_func() if not self.write_only else None
            prop = property(fget=fget, fset=fset, doc=self.doc)
            self.__property = prop
        return self.__property

    @staticmethod
    def __variable_manager_from_obj(obj: C) -> VariableManager[C, V]:
        variable_manager = getattr(obj, VARIABLE_MANAGER_NAME, None)
        if variable_manager is None:
            raise ValueError
        return variable_manager

    def __variable_from_obj(self, obj: C) -> Variable[C, V]:
        variable_manager = self.__variable_manager_from_obj(obj)
        return variable_manager[self.__name]

    def _getter_func(self) -> GetterFunc:
        """Returns the function used as the getter for the property"""

        def wrapper(obj: C) -> Any:
            var = self.__variable_from_obj(obj)
            if var.valid:
                value = var.value
                if self.has_getter_function():
                    # noinspection PyCallingNonCallable
                    value = self.getter_function(obj, value)
                return value

            # Variable is invalid
            computation_successful = True
            try:
                if not self.has_compute_function():
                    raise VariableComputationError("Parameter is invalid and cannot be computed")
                # noinspection PyCallingNonCallable
                value = self.compute_function(obj)
            except Exception as e:
                computation_successful = False
                if not self.use_invalid_value:
                    raise VariableComputationError("Parameter is invalid and cannot be computed") from e
                value = self.invalid_value

            if computation_successful:  # Make only valid if the value was computed, i.e., not the invalid_value
                var.value = value
                var.make_valid()

            if self.has_getter_function():
                # noinspection PyCallingNonCallable
                value = self.getter_function(obj, value)

            return value

        return wrapper

    def _setter_func(self) -> SetterFunc:
        """Returns the function used as the setter for the property"""

        def wrapper(obj, value) -> None:
            var = self.__variable_from_obj(obj)
            if self.has_setter_function():
                # noinspection PyCallingNonCallable
                value = self.setter_function(obj, value)

            var.value = value
            var.make_valid()
            var.invalidate_users()

        return wrapper

    def has_default(self) -> bool:
        """Whether a default is present or not"""
        return self.default_factory is not None or self.default is not None

    def get_default(self) -> V:
        """Get the default value of the variable"""
        if self.default_factory is not None:
            logger.debug("Using default factory on variable '%s'", self.__name)
            return self.default_factory()
        if self.default is not None:
            logger.debug("Using default value on variable '%s'", self.__name)
            return self.default
        logger.debug("No default defined on variable '%s'. Using internal default: %s",
                     self.__name, self.internal_default)
        return self.internal_default

    def build_variable(self) -> Variable[C, V]:
        self.consistency_check()
        var = Variable(self)
        return var


variable = VariablePrototype


class VariablePrototypeManager(Generic[C, V]):

    def __init__(self, *variable_prototype: VariablePrototype[C, V]):
        self._variable_prototypes: dict[str, VariablePrototype[C, V]] = UniqueDict()
        self.add_variable_prototypes(*variable_prototype)

    def add_variable_prototypes(self, *variable_prototype: VariablePrototype[C, V]) -> None:
        """Add variables to the container"""
        for var_proto in variable_prototype:
            self._variable_prototypes[var_proto.get_name()] = var_proto

    def __iter__(self):
        return iter(self._variable_prototypes.values())

    def __getitem__(self, item: str):
        try:
            return self._variable_prototypes[item]
        except KeyError as e:
            raise VariableNotFoundError(item) from e

    def consistency_check(self) -> None:
        """Check the consistency of the container"""
        variable_names = set(self._variable_prototypes.keys())
        dependency_names = set()
        for var in self:
            for dependency in var.depends_on:
                dependency_names.add(dependency)
            for invalidator in var.invalidates:
                dependency_names.add(invalidator)

        if not dependency_names.issubset(variable_names):
            difference = dependency_names.difference(variable_names)
            raise VariableConsistencyError("The following variables are listed as dependencies but were never defined:"
                                           f"{difference}")

    def attach_compute_function(self, variable_prototype_name: str, func: ComputeFunc):
        logger.debug("Attaching compute function to '%s'", variable_prototype_name)
        self[variable_prototype_name].compute_function = func

    def attach_setter_function(self, variable_prototype_name: str, func: SetterFunc):
        logger.debug("Attaching setter function to '%s'", variable_prototype_name)
        self[variable_prototype_name].setter_function = func

    def attach_getter_function(self, variable_prototype_name: str, func: GetterFunc):
        logger.debug("Attaching getter function to '%s'", variable_prototype_name)
        self[variable_prototype_name].getter_function = func

    def attach_function(self, variable_name, function_type: VariableFunctionType, func: Callable):
        if function_type == VariableFunctionType.COMPUTE:
            self.attach_compute_function(variable_name, func)
        elif function_type == VariableFunctionType.SET:
            self.attach_setter_function(variable_name, func)
        elif function_type == VariableFunctionType.GET:
            self.attach_getter_function(variable_name, func)
        else:
            raise VariableInitError(f"VariableFunctionType '{function_type}' not supported")

    def init_functions(self, attribute_dict: dict) -> None:
        """Initialize the functions on the variables.

        This goes through the dict of the object and attaches the marked functions to the variables.
        """
        for attr in attribute_dict.values():
            if not inspect.isfunction(attr):
                continue
            if not (classification := VariableFunctionClassification.check(attr)):
                continue
            self.attach_function(classification.name, classification.param_function_type, attr)

    def build_variable_manager(self) -> VariableManager[C, V]:
        variables = [variable_prototype.build_variable() for variable_prototype in self]
        variable_manager = VariableManager(*variables)
        return variable_manager
