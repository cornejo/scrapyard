#! /usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import wraps
from types import FunctionType
from typing import Any, Callable, TypeVar


T = TypeVar("T")
R = TypeVar("R")


class CallType(str, Enum):
    INSTANCE_METHOD = "method"
    CLASS_METHOD = "classmethod"
    STATIC_METHOD = "staticmethod"
    PROPERTY = "property"


@dataclass
class CallInfo:
    type: CallType
    class_name: str
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


# This class can be used to create mock classes for testing
# The intent is to subclass the real class and override any calls
# relevant to the test. If any unexpected calls are made to the base
# class these will be logged, allowing you to either rework your test
# or override those calls to make your test pass
class SpyBase:
    """Mixin that wraps methods of the original class to log calls."""

    # Update the type annotation to match actual usage (class_name, method_name, args, kwargs)
    _calls: list[CallInfo] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # We have wrapped the first class after SpyBase - so find it
        try:
            spy_index = cls.__mro__.index(SpyBase)
            original_class = cls.__mro__[spy_index + 1]
        except (ValueError, IndexError):
            raise Exception("SpyBase must be used as a mixin with another class")

        for name, attr in original_class.__dict__.items():
            # Skip dunder methods
            if name.startswith("__"):
                continue

            # Skip if already overridden in the subclass
            if name in cls.__dict__:
                continue

            # Handle properties
            if isinstance(attr, property):
                setattr(cls, name, cls._wrap_property(original_class.__name__, name, attr))

            # Handle staticmethod
            elif isinstance(attr, staticmethod):
                static_func = attr.__func__
                wrapped = cls._wrap_static_method(original_class.__name__, name, static_func)
                setattr(cls, name, staticmethod(wrapped))

            # Handle classmethod
            elif isinstance(attr, classmethod):
                class_func: Callable[..., R] = attr.__func__  # type: ignore[attr-defined]
                wrapped = cls._wrap_class_method(original_class.__name__, name, class_func)
                setattr(cls, name, classmethod(wrapped))

            # Handle plain functions (instance methods)
            elif isinstance(attr, FunctionType):
                setattr(cls, name, cls._wrap_instance_method(original_class.__name__, name, attr))

    @classmethod
    def _wrap_instance_method(cls, class_name: str, name: str, method: Callable[..., R]) -> Callable[..., R]:
        @wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
            cls._calls.append(CallInfo(CallType.INSTANCE_METHOD, class_name, name, args, kwargs))
            return method(self, *args, **kwargs)

        return wrapper

    @classmethod
    def _wrap_class_method(cls, class_name: str, name: str, method: Callable[..., R]) -> Callable[..., R]:
        @wraps(method)
        def wrapper(inner_cls: type, *args: Any, **kwargs: Any) -> R:
            cls._calls.append(CallInfo(CallType.CLASS_METHOD, class_name, name, args, kwargs))
            return method(inner_cls, *args, **kwargs)

        return wrapper

    @classmethod
    def _wrap_static_method(cls, class_name: str, name: str, method: Callable[..., R]) -> Callable[..., R]:
        @wraps(method)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            cls._calls.append(CallInfo(CallType.STATIC_METHOD, class_name, name, args, kwargs))
            return method(*args, **kwargs)

        return wrapper

    @classmethod
    def _wrap_property(cls, class_name: str, name: str, prop: property) -> property:
        def getter(self: object) -> Any:
            cls._calls.append(CallInfo(CallType.PROPERTY, class_name, f"{name}.get", (), {}))
            return prop.__get__(self, type(self))

        def setter(self: object, value: Any) -> None:
            cls._calls.append(CallInfo(CallType.PROPERTY, class_name, f"{name}.set", (value,), {}))
            return prop.__set__(self, value)

        def deleter(self: object) -> None:
            cls._calls.append(CallInfo(CallType.PROPERTY, class_name, f"{name}.del", (), {}))
            return prop.__delete__(self)

        return property(
            fget=getter if prop.fget else None,
            fset=setter if prop.fset else None,
            fdel=deleter if prop.fdel else None,
        )

    @classmethod
    def get_calls(cls) -> list[CallInfo]:
        return cls._calls

    @classmethod
    def clear_calls(cls) -> None:
        cls._calls.clear()
