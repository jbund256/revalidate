# coding=utf-8
"""Custom exception classes"""


class VariableException(Exception):
    """Generic exception in the package"""


class VariableInitError(VariableException):
    ...


class VariableComputationError(VariableException):
    ...


class VariableNotFoundError(VariableException):

    def __init__(self, name: str):
        super().__init__(f"Parameter with name '{name}' was not found")


class VariableRenameError(VariableException):

    def __init__(self, old_name, new_name):
        super().__init__(f"Variable cannot be renamed. Current name is '{old_name}'. Cannot rename to '{new_name}'")


class VariableConsistencyError(VariableException):
    ...
