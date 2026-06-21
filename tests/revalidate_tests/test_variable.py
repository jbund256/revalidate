# coding=utf-8
import pytest

from revalidate import Variable, VariableBase, variable
from revalidate.constants import VARIABLE_MANAGER_NAME
from revalidate.exceptions import VariableConsistencyError
from revalidate.variable import INVALID, VariableManager
from revalidate.variable_prototype import VariablePrototype


def test_valid():
    """Test if the valid field is set properly"""
    var = Variable(VariablePrototype())
    assert not var.valid
    var.make_valid()
    assert var.valid
    var.make_invalid()
    assert not var.valid


def test_prototype():
    """Test if the prototype object is set properly"""
    prototype = VariablePrototype()
    var = Variable(prototype)

    assert var.prototype is prototype


def test_name():
    prototype = VariablePrototype()
    prototype.set_name("name")
    var = Variable(prototype)
    assert var.name == "name"


@pytest.mark.parametrize("prototype, value, valid",
                         [(VariablePrototype(), INVALID, False),
                          (VariablePrototype(default=4), 4, True),
                          (VariablePrototype(default_factory=lambda: 4), 4, True)])
def test_init_value(prototype, value, valid):
    """Test the value initialization"""
    var = Variable(prototype)

    assert var.value == value
    assert var.valid == valid


def test_eq():
    prototype_1 = VariablePrototype()
    prototype_2 = VariablePrototype()
    prototype_3 = VariablePrototype()

    prototype_1.set_name("A")
    prototype_2.set_name("A")
    prototype_3.set_name("B")

    var_1 = Variable(prototype_1)
    var_2 = Variable(prototype_2)
    var_3 = Variable(prototype_3)

    assert var_1 == var_2
    assert var_1 != var_3
    assert var_2 != var_3


class UserTestHelper:

    def __init__(self, *vars):
        self.vars = vars

    def make_valid(self):
        for var in self.vars:
            var.make_valid()

    def check(self, *validity):
        for var, valid in zip(self.vars, validity, strict=True):
            assert var.valid == valid


class TestUsers:
    """Test class for testing users on variables"""

    @staticmethod
    def get_var(name: str):
        prototype = VariablePrototype()
        prototype.set_name(name)
        return Variable(prototype)

    @pytest.fixture
    def var_1(self):
        return self.get_var("var_1")

    @pytest.fixture
    def var_2(self):
        return self.get_var("var_2")

    @pytest.fixture
    def var_3(self):
        return self.get_var("var_3")

    def test_add(self, var_1, var_2, var_3):
        assert len(var_1.get_users()) == 0

        var_1.add_user(var_2)
        assert len(var_1.get_users()) == 1
        assert var_1.get_users()[0] is var_2

        var_1.add_user(var_3)
        assert len(var_1.get_users()) == 2
        assert var_2 in var_1.get_users()
        assert var_3 in var_1.get_users()

        var_1.add_user(var_1)
        assert len(var_1.get_users()) == 2
        assert var_2 in var_1.get_users()
        assert var_3 in var_1.get_users()

        var_1.add_user(var_3)
        assert len(var_1.get_users()) == 2
        assert var_2 in var_1.get_users()
        assert var_3 in var_1.get_users()

    def test_remove(self, var_1, var_2, var_3):
        var_1.add_user(var_2)
        var_1.add_user(var_3)

        assert len(var_1.get_users()) == 2
        assert var_2 in var_1.get_users()
        assert var_3 in var_1.get_users()

        var_1.remove_user(var_2)
        assert len(var_1.get_users()) == 1
        assert var_1.get_users()[0] is var_3

        var_1.remove_user(var_3)
        assert len(var_1.get_users()) == 0

    def test_reset(self, var_1, var_2, var_3):
        var_1.add_user(var_2)
        var_1.add_user(var_3)

        assert len(var_1.get_users()) == 2
        assert var_2 in var_1.get_users()
        assert var_3 in var_1.get_users()

        var_1.reset_users()
        assert len(var_1.get_users()) == 0

    def test_invalidate_users_0(self):
        """Case without users"""
        uth = UserTestHelper(*[var_1 := self.get_var("1"),
                               self.get_var("2")])
        uth.make_valid()

        var_1.invalidate_users()

        uth.check(True, True)

    def test_invalidate_users_1(self):
        """Case 1(2)"""
        uth = UserTestHelper(*[var_1 := self.get_var("1"),
                               var_2 := self.get_var("2")])
        uth.make_valid()

        var_2.add_user(var_1)
        var_2.invalidate_users()

        uth.check(False, True)

        var_1.make_valid()
        var_1.invalidate_users()

        uth.check(True, True)

    def test_invalidate_users_2(self):
        """Case 1(2) and 2(1)"""
        uth = UserTestHelper(*[var_1 := self.get_var("1"),
                               var_2 := self.get_var("2")])
        uth.make_valid()

        var_1.add_user(var_2)
        var_2.add_user(var_1)

        var_1.invalidate_users()
        uth.check(True, False)

    def test_invalidate_users_3(self):
        """Case 1(2), 2(3) and 3(4). A chain"""
        uth = UserTestHelper(*[var_1 := self.get_var("1"),
                               var_2 := self.get_var("2"),
                               var_3 := self.get_var("3"),
                               var_4 := self.get_var("4")])

        var_2.add_user(var_1)
        var_3.add_user(var_2)
        var_4.add_user(var_3)

        uth.make_valid()
        var_1.invalidate_users()

        uth.check(True, True, True, True)

        uth.make_valid()
        var_2.invalidate_users()

        uth.check(False, True, True, True)

        uth.make_valid()
        var_4.invalidate_users()

        uth.check(False, False, False, True)

    def test_invalidate_users_4(self):
        """Case 1(2), 2(3), 3(2) and 3(4). A chain"""
        uth = UserTestHelper(*[var_1 := self.get_var("1"),
                               var_2 := self.get_var("2"),
                               var_3 := self.get_var("3"),
                               var_4 := self.get_var("4")])

        var_2.add_user(var_1, var_3)
        var_3.add_user(var_2)
        var_4.add_user(var_3)

        uth.make_valid()
        var_1.invalidate_users()
        uth.check(True, True, True, True)

        uth.make_valid()
        var_2.invalidate_users()
        uth.check(False, True, False, True)

        uth.make_valid()
        var_3.invalidate_users()
        uth.check(False, False, True, True)

        uth.make_valid()
        var_4.invalidate_users()
        uth.check(False, False, False, True)

    def test_invalidate_users_5(self):
        """Case 1(2), 2(3) and 3(1). A circle"""
        uth = UserTestHelper(*[var_1 := self.get_var("1"),
                               var_2 := self.get_var("2"),
                               var_3 := self.get_var("3")])

        var_1.add_user(var_3)
        var_2.add_user(var_1)
        var_3.add_user(var_2)

        uth.make_valid()
        var_1.invalidate_users()
        uth.check(True, False, False)

        uth.make_valid()
        var_2.invalidate_users()
        uth.check(False, True, False)

        uth.make_valid()
        var_3.invalidate_users()
        uth.check(False, False, True)

    def test_invalidate_users_6(self):
        """Case 1(2), 2(3, 4). A tree"""
        uth = UserTestHelper(*[var_1 := self.get_var("1"),
                               var_2 := self.get_var("2"),
                               var_3 := self.get_var("3"),
                               var_4 := self.get_var("4")])

        var_2.add_user(var_1)
        var_3.add_user(var_2)
        var_4.add_user(var_2)

        uth.make_valid()
        var_1.invalidate_users()
        uth.check(True, True, True, True)

        uth.make_valid()
        var_2.invalidate_users()
        uth.check(False, True, True, True)

        uth.make_valid()
        var_3.invalidate_users()
        uth.check(False, False, True, True)

        uth.make_valid()
        var_4.invalidate_users()
        uth.check(False, False, True, True)


class ValidityChecker(VariableBase, debug=True):
    var_1 = variable(default=3)
    var_2 = variable(depends_on=["var_1"])

    def __getitem__(self, item):
        return self.__getattribute__(VARIABLE_MANAGER_NAME)[item]


def test_valid_in_class():
    val_checker = ValidityChecker()
    assert val_checker["var_1"].valid
    assert not val_checker["var_2"].valid
    val_checker.var_2 = 2

    assert val_checker["var_2"].valid
    val_checker.var_1 = 4
    assert val_checker["var_1"].valid
    assert not val_checker["var_2"].valid


class TestVariableManager:

    def test_init(self):
        prototype = VariablePrototype()
        prototype.set_name("name")
        var = Variable(prototype)

        # Empty creation
        var_manager = VariableManager()

        var_manager = VariableManager(var)

        var_manager = VariableManager()
        with pytest.raises(VariableConsistencyError):
            var_manager.add_variable(Variable(VariablePrototype()))

        var_manager.add_variable(var)

    def test_iter(self):
        prototype = VariablePrototype()
        prototype.set_name("name_1")
        var_1 = Variable(prototype)

        prototype = VariablePrototype()
        prototype.set_name("name_2")
        var_2 = Variable(prototype)

        var_manager = VariableManager(var_1, var_2)
        for var in var_manager:
            assert isinstance(var, Variable)

        assert len(tuple(iter(var_manager))) == 2
        assert var_1 in tuple(iter(var_manager))
        assert var_2 in tuple(iter(var_manager))

    def test_getitem(self):
        prototype = VariablePrototype()
        prototype.set_name("name_1")
        var_1 = Variable(prototype)

        prototype = VariablePrototype()
        prototype.set_name("name_2")
        var_2 = Variable(prototype)

        var_manager = VariableManager(var_1, var_2)

        assert var_manager["name_1"] is var_1
        assert var_manager["name_2"] is var_2

    def test_init_dependencies_0(self):
        prototype_1 = VariablePrototype()
        prototype_1.set_name("1")

        prototype_2 = VariablePrototype()
        prototype_2.set_name("2")

        var_1 = Variable(prototype_1)
        var_2 = Variable(prototype_2)

        var_manager = VariableManager(var_1, var_2)
        var_manager.init_dependencies()

        assert len(var_1.get_users()) == 0
        assert len(var_2.get_users()) == 0

    def test_init_dependencies_1(self):
        prototype_1 = VariablePrototype(depends_on=["2"])
        prototype_1.set_name("1")

        prototype_2 = VariablePrototype(depends_on=["1"])
        prototype_2.set_name("2")

        var_1 = Variable(prototype_1)
        var_2 = Variable(prototype_2)

        var_manager = VariableManager(var_1, var_2)
        var_manager.init_dependencies()

        assert len(var_1.get_users()) == 1
        assert var_1.get_users()[0] is var_2

        assert len(var_2.get_users()) == 1
        assert var_2.get_users()[0] is var_1

    def test_init_dependencies_2(self):
        prototype_1 = VariablePrototype(invalidates=["2"])
        prototype_1.set_name("1")

        prototype_2 = VariablePrototype(invalidates=["1"])
        prototype_2.set_name("2")

        var_1 = Variable(prototype_1)
        var_2 = Variable(prototype_2)

        var_manager = VariableManager(var_1, var_2)
        var_manager.init_dependencies()

        assert len(var_1.get_users()) == 1
        assert var_1.get_users()[0] is var_2

        assert len(var_2.get_users()) == 1
        assert var_2.get_users()[0] is var_1

    def test_init_dependencies_3(self):
        prototype_1 = VariablePrototype(depends_on=["2"])
        prototype_1.set_name("1")

        prototype_2 = VariablePrototype()
        prototype_2.set_name("2")

        var_1 = Variable(prototype_1)
        var_2 = Variable(prototype_2)

        var_manager = VariableManager(var_1, var_2)
        var_manager.init_dependencies()

        assert len(var_1.get_users()) == 0

        assert len(var_2.get_users()) == 1
        assert var_2.get_users()[0] is var_1

    def test_init_dependencies_4(self):
        prototype_1 = VariablePrototype(invalidates=["2"])
        prototype_1.set_name("1")

        prototype_2 = VariablePrototype()
        prototype_2.set_name("2")

        var_1 = Variable(prototype_1)
        var_2 = Variable(prototype_2)

        var_manager = VariableManager(var_1, var_2)
        var_manager.init_dependencies()

        assert len(var_1.get_users()) == 1
        assert var_1.get_users()[0] is var_2

        assert len(var_2.get_users()) == 0

    def test_consistency_check_0(self):
        prototype_1 = VariablePrototype()
        prototype_1.set_name("1")

        prototype_2 = VariablePrototype()
        prototype_2.set_name("2")

        var_1 = Variable(prototype_1)
        var_2 = Variable(prototype_2)

        var_manager = VariableManager(var_1, var_2)
        var_manager.consistency_check()

    def test_consistency_check_1(self):
        prototype_1 = VariablePrototype(depends_on=["3"])
        prototype_1.set_name("1")

        prototype_2 = VariablePrototype()
        prototype_2.set_name("2")

        var_1 = Variable(prototype_1)
        var_2 = Variable(prototype_2)

        var_manager = VariableManager(var_1, var_2)
        with pytest.raises(VariableConsistencyError):
            var_manager.consistency_check()
