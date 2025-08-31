#! /usr/bin/env python3

from functools import wraps
from typing import Any, Callable, TypeVar


T = TypeVar("T")
R = TypeVar("R")


class MyClass:
    def greet(self, name: str) -> str:
        return f"Hello, {name}!"


# This class can be used to create mock classes for testing
# The intent is to subclass the real class and override any calls
# relevant to the test. If any unexpected calls are made to the base
# class these will be logged, allowing you to either rework your test
# or override those calls to make your test pass
class SpyBase:
    """Mixin that wraps methods of the original class to log calls."""

    # Update the type annotation to match actual usage (class_name, method_name, args, kwargs)
    _calls: list[tuple[str, str, tuple[Any, ...], dict[str, Any]]] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # We have wrapped the first class after SpyBase - so find it
        try:
            spy_index = cls.__mro__.index(SpyBase)
            original_class = cls.__mro__[spy_index + 1]
        except (ValueError, IndexError):
            raise Exception("SpyBase must be used as a mixin with another class")

        for name, attr in original_class.__dict__.items():
            # only wrap callables, skip dunders, skip if redefined in subclass
            if (
                callable(attr)
                and not name.startswith("__")
                and name not in cls.__dict__  # <-- skip if subclass overrides
            ):
                setattr(cls, name, cls._wrap_method(original_class.__name__, name, attr))

    @classmethod
    def _wrap_method(cls, class_name: str, name: str, method: Callable[..., R]) -> Callable[..., R]:
        @wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
            cls._calls.append((class_name, name, args, kwargs))
            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def get_calls(cls) -> list[tuple[str, str, tuple[Any, ...], dict[str, Any]]]:
        return cls._calls

    @classmethod
    def reset_calls(cls) -> None:
        cls._calls.clear()


class SpyMyClass(SpyBase, MyClass):
    # Redefine greet -> won't be wrapped/logged
    def greet(self, name: str) -> str:
        return f"[SPY OVERRIDE] {name}"


if __name__ == "__main__":
    a = MyClass()
    print(a.greet("Alice"))  # "Hello, Alice!"

    b = SpyMyClass()
    print(b.greet("Bob"))  # "[SPY OVERRIDE] Bob"

    print(SpyMyClass.get_calls())  # [('greet', ('Bob',), {})]

    print("Logged calls:", SpyMyClass.get_calls())
