# coding=utf-8
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, Optional, Self

from .exceptions import VariableConsistencyError, VariableNotFoundError
from .typing import INVALID, C, V
from .utils import UniqueDict

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .variable_prototype import VariablePrototype


@dataclass
class Variable(Generic[C, V]):
    prototype: "VariablePrototype[C, V]"

    value: Any = field(default=INVALID, init=False,)
    valid: bool = field(default=False, init=False)
    _users: set[Self] = field(default_factory=set)

    def __post_init__(self):
        self.init_value()

    def init_value(self) -> None:
        """Initialize the internal variable that is saved on the object

        The internal name must not already exist on the object.
        If a default is provided by the user, the variable is considered valid, otherwise invalid.
        """
        logger.debug("Initializing internal variables of variable '%s'", self.name)
        self.value = self.prototype.get_default()

        if self.prototype.has_default():
            logger.debug("Initialized variable is valid (variable '%s')", self.name)
            self.make_valid()
        else:
            logger.debug("Initialized variable is invalid (variable '%s')", self.name)
            self.make_invalid()

    @property
    def name(self):
        return self.prototype.get_name()

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name

    def make_valid(self) -> None:
        """Marc the variable as valid"""
        self.valid = True

    def make_invalid(self) -> None:
        """Marc the variable as invalid"""
        self.valid = False

    def __repr__(self):
        return f"Variable {self.name}"

    def add_user(self, *user_variable: Self):
        """Add a user variable to the current one.

        When the current variable changes, the user variable becomes invalid.
        """
        for user_var in user_variable:
            if user_var is self:
                logger.warning("Trying to add self to users. Skipping self.")
                continue
            logger.debug("Adding '%s' as a user of '%s'", user_var.name, self.name)
            self._users.add(user_var)

    def remove_user(self, user_variable: Self) -> None:
        """Remove a user variable"""
        logger.debug("Removing user '%s'", user_variable.name)
        self._users.remove(user_variable)

    def reset_users(self) -> None:
        """Reset all user variables"""
        self._users = set()

    def get_users(self) -> tuple[Self]:
        """Get all user variables"""
        return tuple(self._users)

    def invalidate_users(self, seen: Optional[set[str]] = None) -> None:
        """Make all user variables invalid"""
        if seen is None:
            seen = set()
            seen.add(self.name)
            logger.debug("Start of new invalidate call from '%s'", self.name)

        for user in self._users:
            if user.name in seen:
                continue
            user.make_invalid()
            logger.debug("Change of variable '%s'. User variable '%s' becomes invalid", self.name, user.name)
            seen.add(user.name)
            user.invalidate_users(seen)

    # def _invalidate_users_except_dependencies(self) -> None:
    #     """Make all user variables invalid"""
    #     for user in self._users:
    #         if user.name in self.depends_on:
    #             continue
    #         logger.debug("Change of variable '%s'. User variable '%s' becomes invalid", self.name, user.name)
    #         user.make_invalid()


class VariableManager(Generic[C, V]):
    """Container class for a group of variables defined on a class"""

    def __init__(self, *variable: Variable[C, V]):
        self._variables: dict[str, Variable[C, V]] = UniqueDict()
        self.add_variable(*variable)

    def __iter__(self):
        return iter(self._variables.values())

    def __getitem__(self, item: str):
        try:
            return self._variables[item]
        except KeyError as e:
            raise VariableNotFoundError(item) from e

    def __getattr__(self, item):
        return self._variables[item]

    def add_variable(self, *variable: Variable[C, V]) -> None:
        """Add variables to the container"""
        for var in variable:
            if not isinstance(var.name, str):
                raise VariableConsistencyError("The variable needs a proper name")
            self._variables[var.name] = var

    def init_dependencies(self) -> None:
        """Initialize the dependencies between all variables"""
        for var in self:
            var.reset_users()

        for var in self:
            for dependency in var.prototype.depends_on:
                self._variables[dependency].add_user(var)

            for to_invalidate in var.prototype.invalidates:
                var.add_user(self._variables[to_invalidate])

    def consistency_check(self) -> None:
        """Check the consistency of the container"""
        variable_names = set(self._variables.keys())
        dependency_names = set()
        for var in self:
            for dependency in var.prototype.depends_on:
                dependency_names.add(dependency)

        if not dependency_names.issubset(variable_names):
            difference = dependency_names.difference(variable_names)
            raise VariableConsistencyError("The following variables are listed as dependencies but were never defined:"
                                           f"{difference}")
