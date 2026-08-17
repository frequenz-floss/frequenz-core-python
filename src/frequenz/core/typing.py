# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Type hints and utility functions for type checking and types.

This module provides a decorator to disable the `__init__` constructor of a class, to
force the use of a factory method to create instances. See
[`@disable_init`][frequenz.core.typing.disable_init] for more information.

It also provides a metaclass used by the decorator to disable the `__init__`:
[`NoInitConstructibleMeta`][frequenz.core.typing.NoInitConstructibleMeta]. This is
useful mostly for disabling `__init__` while having to use another metaclass too (like
[`abc.ABCMeta`][abc.ABCMeta]).

Finally, it provides [`FloatInt`][frequenz.core.typing.FloatInt], an honest type alias
for `float | int`, to annotate floating point values that can also be an `int` at
runtime.
"""

from collections.abc import Callable
from typing import Any, NoReturn, TypeAlias, TypeVar, cast, overload

FloatInt: TypeAlias = float | int
"""A floating point value that can also be an `int` at runtime.

[PEP 484's numeric tower](https://peps.python.org/pep-0484/#the-numeric-tower) makes
`int` assignable to any `float`-annotated parameter, attribute or variable, so a plain
`float` annotation is a lie: type checkers (even `mypy --strict`) happily accept `int`
values, but `isinstance(1, float)` is `False` at runtime. This breaks `match … case
float():` arms (an `int` value falls through to
[`assert_never()`][typing.assert_never]), calls to `float`-only methods like
[`hex()`][float.hex], and any other code dispatching on the concrete runtime type.

Annotating with this alias instead makes the heterogeneity explicit, so type checkers
push the code reading these values to handle both branches, typically by matching with
`case float() | int():`.

The full analysis, including the alternatives that were rejected, is recorded in
[issue #250](https://github.com/frequenz-floss/frequenz-client-common-python/issues/250).

Danger:
    `bool` is a subclass of `int`, so `True` and `False` also satisfy this alias. This
    is inherent to Python's type system and is not guarded against.

Example:
    ```python
    from typing import assert_never

    from frequenz.core.typing import FloatInt


    def describe(value: FloatInt | None) -> str:
        match value:
            case float() | int():
                return f"number {value}"
            case None:
                return "nothing"
            case unexpected:
                assert_never(unexpected)


    assert describe(1) == "number 1"
    assert describe(1.5) == "number 1.5"
    assert describe(None) == "nothing"
    ```
"""


TypeT = TypeVar("TypeT", bound=type)
"""A type variable that is bound to a type."""


@overload
def disable_init(
    cls: None = None,
    *,
    error: Exception | None = None,
) -> Callable[[TypeT], TypeT]: ...


@overload
def disable_init(cls: TypeT) -> TypeT: ...


def disable_init(
    cls: TypeT | None = None,
    *,
    error: Exception | None = None,
) -> TypeT | Callable[[TypeT], TypeT]:
    """Disable the `__init__` constructor of a class.

    This decorator can be used to disable the `__init__` constructor of a class. It is
    intended to be used with classes that don't provide a default constructor and
    require the use of a factory method to create instances.

    When marking a class with this decorator, the class cannot be even declared with a
    `__init__` method, as it will raise a `TypeError` when the class is created, as soon
    as the class is parsed by the Python interpreter. It will also raise a `TypeError`
    when the `__init__` method is called.

    To create an instance you must provide a factory method, using `__new__`.

    Warning:
        This decorator will use a custom metaclass to disable the `__init__` constructor
        of the class, so if your class already uses a custom metaclass, you should be
        aware of potential conflicts. See
        [`NoInitConstructibleMeta`][frequenz.core.typing.NoInitConstructibleMeta] for an
        example on how to use more than one metaclass.

        It is also recommended to apply this decorator only to classes inheriting from
        `object` directly (i.e. not explicitly inheriting from any other classes), as
        things can also get tricky when applying the constructor to a sub-class for the
        first time.

    Example: Basic example defining a class with a factory method
        To be able to type hint the class correctly, you can declare the instance
        attributes in the class body, and then use a factory method to create instances.

        ```python
        from typing import Self

        @disable_init
        class MyClass:
            value: int

            @classmethod
            def new(cls, value: int = 1) -> Self:
                self = cls.__new__(cls)
                self.value = value
                return self

        instance = MyClass.new()

        # Calling the default constructor (__init__) will raise a TypeError
        try:
            instance = MyClass()
        except TypeError as e:
            print(e)
        ```

    Example: Class wrongly providing an `__init__` constructor
        ```python
        try:
            @disable_init
            class MyClass:
                def __init__(self) -> None:
                    pass
        except TypeError as e:
            assert isinstance(e, TypeError)
            print(e)
        ```

    Example: Using a custom error message when the default constructor is called
        ```python
        from typing import Self

        class NoInitError(TypeError):
            def __init__(self) -> None:
                super().__init__("Please create instances of MyClass using MyClass.new()")

        @disable_init(error=NoInitError())
        class MyClass:
            @classmethod
            def new(cls) -> Self:
                return cls.__new__(cls)

        try:
            instance = MyClass()
        except NoInitError as e:
            assert str(e) == "Please create instances of MyClass using MyClass.new()"
            print(e)
        ```

    Args:
        cls: The class to be decorated.
        error: The error to raise if __init__ is called, if `None` a default
            [TypeError][] will be raised.

    Returns:
        A decorator that disables the `__init__` constructor of `cls`.
    """

    def decorator(inner_cls: TypeT) -> TypeT:
        return cast(
            TypeT,
            NoInitConstructibleMeta(
                inner_cls.__name__,
                inner_cls.__bases__,
                dict(inner_cls.__dict__),
                no_init_constructible_error=error,
            ),
        )

    if cls is None:
        return decorator
    return decorator(cls)


class NoInitConstructibleMeta(type):
    """A metaclass that disables the `__init__` constructor.

    This metaclass can be used to disable the `__init__` constructor of a class. It is
    intended to be used with classes that don't provide a default constructor and
    require the use of a factory method to create instances.

    When marking a class using this metaclass, the class cannot be even declared with a
    `__init__` method, as it will raise a `TypeError` when the class is created, as soon
    as the class is parsed by the Python interpreter. It will also raise a `TypeError`
    when the `__init__` method is called.

    To create an instance you must provide a factory method, using `__new__`.

    Warning:
        It is also recommended to apply this metaclass only to classes inheriting from
        `object` directly (i.e. not explicitly inheriting from any other classes), as
        things can also get tricky when applying the constructor to a sub-class for the
        first time.

    Example: Basic example defining a class with a factory method
        To be able to type hint the class correctly, you can declare the instance
        attributes in the class body, and then use a factory method to create instances.

        ```python
        from typing import Self

        class MyClass(metaclass=NoInitConstructibleMeta):
            value: int

            @classmethod
            def new(cls, value: int = 1) -> Self:
                self = cls.__new__(cls)
                self.value = value
                return self

        instance = MyClass.new()

        # Calling the default constructor (__init__) will raise a TypeError
        try:
            instance = MyClass()
        except TypeError as e:
            print(e)
        ```

        Hint:
            The [`@disable_init`][frequenz.core.typing.disable_init] decorator is a more
            convenient way to use this metaclass.

    Example: Example combining with other metaclass
        A typical case where you might want this is to combine with
        [`abc.ABCMeta`][abc.ABCMeta] to create an abstract class that doesn't provide a
        default constructor.

        ```python
        from abc import ABCMeta, abstractmethod
        from typing import Self

        class NoInitConstructibleABCMeta(ABCMeta, NoInitConstructibleMeta):
            pass

        class MyAbstractClass(metaclass=NoInitConstructibleABCMeta):
            @abstractmethod
            def do_something(self) -> None:
                ...

        class MyClass(MyAbstractClass):
            value: int

            @classmethod
            def new(cls, value: int = 1) -> Self:
                self = cls.__new__(cls)
                self.value = value
                return self

            def do_something(self) -> None:
                print("Doing something")

        instance = MyClass.new()
        instance.do_something()

        # Calling the default constructor (__init__) will raise a TypeError
        try:
            instance = MyClass()
        except TypeError as e:
            print(e)
        ```

    """

    # We need to use noqa here because pydoclint can't figure out that
    # _get_no_init_constructible_error() returns a TypeError.
    def __new__(  # noqa: DOC503
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        """Create a new class with a disabled __init__ constructor.

        Args:
            name: The name of the new class.
            bases: The base classes of the new class.
            namespace: The namespace of the new class.
            **kwargs: Additional keyword arguments.

        Returns:
            The new class with a disabled __init__ constructor.

        Raises:
            TypeError: If the class provides a default constructor.
        """
        if "__init__" in namespace:
            raise _get_no_init_constructible_error(name, bases, **kwargs)
        return super().__new__(mcs, name, bases, namespace)

    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """Initialize the new class."""
        super().__init__(name, bases, namespace)
        cls._no_init_constructible_error = kwargs.get("no_init_constructible_error")

    # We need to use noqa here because pydoclint can't figure out that
    # _get_no_init_constructible_error() returns a TypeError.
    def __call__(cls, *args: Any, **kwargs: Any) -> NoReturn:  # noqa: DOC503
        """Raise an error when the __init__ constructor is called.

        Args:
            *args: ignored positional arguments.
            **kwargs: ignored keyword arguments.

        Raises:
            TypeError: Always.
        """
        raise _get_no_init_constructible_error(
            cls.__name__,
            cls.__bases__,
            no_init_constructible_error=cls._no_init_constructible_error,
        )


def _get_no_init_constructible_error(
    name: str, bases: tuple[type, ...], **kwargs: Any
) -> Exception:
    error = kwargs.get("no_init_constructible_error")
    if error is None:
        for base in bases:
            if attr := getattr(base, "_no_init_constructible_error", None):
                error = attr
                break
        else:
            error = TypeError(
                f"{name} doesn't provide a default constructor, you must use a "
                "factory method to create instances."
            )
    assert isinstance(error, Exception)
    return error
