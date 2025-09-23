import pytest

from spybase import CallType, SpyBase


class SpyTestException(Exception):
    pass


# --------------------
# Demo class under test
# --------------------
class MyTestClass:
    def __init__(self):
        self.normal_val = 0

    def instance_method_normal(self, x: int) -> int:
        return x + 1

    def instance_method_towrap(self, x: int) -> int:
        return x - 1

    @staticmethod
    def static_method_normal(x: int) -> int:
        return x * 2

    @staticmethod
    def static_method_towrap(x: int) -> int:
        return x * -1

    @classmethod
    def class_method_normal(cls, x: int) -> int:
        return x + 100

    @classmethod
    def class_method_towrap(cls, x: int) -> int:
        return x - 100

    @property
    def property_normal(self) -> int:
        return 42

    @property_normal.setter
    def property_normal(self, v: int) -> None:
        self.normal_val = v

    @property_normal.deleter
    def property_normal(self) -> None:
        self.normal_val = None

    @property
    def property_towrap(self) -> int:
        return -1

    @property_towrap.setter
    def property_towrap(self, v: int) -> None:
        self.wrapped_val = v

    @property_towrap.deleter
    def property_towrap(self) -> None:
        self.wrapped_val = None


# This class wraps the class under test. For methods it explicitly defines
# no logs will be captured. If any other methods are called then these will
# be logged so the test can be refined later. The intent is to make a class
# that can be used while trying to identify how to properly mock out
# an object so that no 'other' methods are called
class SpyTestClass(SpyBase, MyTestClass):
    def instance_method_towrap(self, x: int) -> int:
        return 5

    @staticmethod
    def static_method_towrap(x: int) -> int:
        return 6

    @classmethod
    def class_method_towrap(cls, x: int) -> int:
        return 7

    @property
    def property_towrap(self) -> int:
        return 8

    @property_towrap.setter
    def property_towrap(self, v: int) -> None:
        raise SpyTestException("setter")

    @property_towrap.deleter
    def property_towrap(self) -> None:
        raise SpyTestException("deleter")


# --------------------
# Tests
# --------------------
def test_instance_method_logged():
    SpyBase.clear_calls()

    s = SpyTestClass()

    # This will be arg + 1
    assert 2 == s.instance_method_normal(1)
    assert 5 == s.instance_method_normal(4)

    # These will always be 5
    assert 5 == s.instance_method_towrap(1)
    assert 5 == s.instance_method_towrap(999)

    # Only instance_method_normal should be logged, since it wasn't overridden
    calls = SpyBase.get_calls()
    assert len(calls) == 2
    assert all(c.type == CallType.INSTANCE_METHOD for c in calls)
    assert all(c.class_name == "MyTestClass" for c in calls)
    assert all(c.name == "instance_method_normal" for c in calls)
    assert calls[0].args == (1,)
    assert calls[1].args == (4,)
    assert all(c.kwargs == {} for c in calls)


def test_static_method_logged():
    SpyBase.clear_calls()

    s = SpyTestClass()

    # This will be arg * 2
    assert 2 == s.static_method_normal(1)
    assert 8 == s.static_method_normal(4)

    # These will always be 6
    assert 6 == s.static_method_towrap(1)
    assert 6 == s.static_method_towrap(999)

    # Only static_method_normal should be logged, since it wasn't overridden
    calls = SpyBase.get_calls()
    assert len(calls) == 2
    assert all(c.type == CallType.STATIC_METHOD for c in calls)
    assert all(c.class_name == "MyTestClass" for c in calls)
    assert all(c.name == "static_method_normal" for c in calls)
    assert calls[0].args == (1,)
    assert calls[1].args == (4,)
    assert all(c.kwargs == {} for c in calls)


def test_class_method_logged():
    SpyBase.clear_calls()

    s = SpyTestClass()

    # This will be arg + 100
    assert 101 == s.class_method_normal(1)
    assert 104 == s.class_method_normal(4)

    # These will always be 7
    assert 7 == s.class_method_towrap(1)
    assert 7 == s.class_method_towrap(999)

    # Only class_method_normal should be logged, since it wasn't overridden
    calls = SpyBase.get_calls()
    assert len(calls) == 2
    assert all(c.type == CallType.CLASS_METHOD for c in calls)
    assert all(c.class_name == "MyTestClass" for c in calls)
    assert all(c.name == "class_method_normal" for c in calls)
    assert calls[0].args == (1,)
    assert calls[1].args == (4,)
    assert all(c.kwargs == {} for c in calls)


def test_properties_logged():
    SpyBase.clear_calls()

    s = SpyTestClass()

    assert 42 == s.property_normal
    assert 0 == s.normal_val
    s.property_normal = 99
    assert 99 == s.normal_val
    del s.property_normal
    assert s.normal_val is None

    assert 8 == s.property_towrap
    with pytest.raises(SpyTestException, match="setter"):
        s.property_towrap = 99
    with pytest.raises(SpyTestException, match="deleter"):
        del s.property_towrap

    # Only class_method_normal should be logged, since it wasn't overridden
    calls = SpyBase.get_calls()
    assert len(calls) == 3
    assert all(c.type == CallType.PROPERTY for c in calls)
    assert all(c.class_name == "MyTestClass" for c in calls)
    assert calls[0].name == "property_normal.get"
    assert calls[1].name == "property_normal.set"
    assert calls[2].name == "property_normal.del"
    assert calls[0].args == ()
    assert calls[1].args == (99,)
    assert calls[2].args == ()
    assert all(c.kwargs == {} for c in calls)
