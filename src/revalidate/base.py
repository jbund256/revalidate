# coding=utf-8
"""The base classes"""

from .variable import VariableManager
from .variable_prototype import VariablePrototype, VariablePrototypeManager
from .constants import VARIABLE_MANAGER_NAME, VARIABLE_PROTOTYPE_MANAGER_NAME


class VariableDict(dict):

    def __init__(self):
        super().__init__()
        self.__variables: list[VariablePrototype]= []

    def variables(self) -> tuple[VariablePrototype]:
        return tuple(self.__variables)

    def __setitem__(self, key, value):
        if isinstance(value, VariablePrototype):
            value.set_name(key)
            self.__variables.append(value)
            value = value.get_property()
        super().__setitem__(key, value)


class VariableMeta(type):

    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        return VariableDict()

    def __init__(cls, name, bases, namespace, **kwargs):
        super().__init__(name, bases, namespace)
        if cls.__name__ == "VariableBase":
            return
        namespace: VariableDict
        # debug = kwargs.get("debug", False)
        variable_prototype_manager = VariablePrototypeManager(*namespace.variables())
        variable_prototype_manager.init_functions(cls.__dict__)
        variable_prototype_manager.consistency_check()
        setattr(cls, VARIABLE_PROTOTYPE_MANAGER_NAME, variable_prototype_manager)


class VariableBase(metaclass=VariableMeta):

    # Runs on class creation
    def __init_subclass__(cls, debug: bool = False, **kwargs):
        super().__init_subclass__(**kwargs)
        # cls._debug = debug

    # Runs on object creation
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        variable_prototype_manager: VariablePrototypeManager = getattr(obj, VARIABLE_PROTOTYPE_MANAGER_NAME)
        variable_manager: VariableManager = variable_prototype_manager.build_variable_manager()
        variable_manager.init_dependencies()
        variable_manager.consistency_check()

        obj._variable_manager = variable_manager

        return obj

    def __getattr__(self, item):
        if item == VARIABLE_MANAGER_NAME:
            return self._variable_manager
        raise AttributeError
