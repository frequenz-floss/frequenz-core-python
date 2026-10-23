# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Enum utilities with support for deprecated members.

This module provides an [`Enum`][frequenz.core.enum.Enum] base class that extends the
standard library's [`enum.Enum`][] to support marking certain members as deprecated.

See the [class documentation][frequenz.core.enum.Enum] for details and examples.
"""

from __future__ import annotations

import enum
import warnings
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Self, TypeVar, cast, overload

# Note: This module contains more casts and uses of Any than what's typically
# ideal. This is because type hinting EnumType and Enum subclasses is quite
# challenging, as there is a lot of special behavior in `mypy` for these classes.
#
# The resulting enum should be treated as a regular enum by mypy, so hopefully everthing
# still works as expected.

EnumT = TypeVar("EnumT", bound=enum.Enum)
"""Type variable for enum types."""


ValueT = TypeVar("ValueT")
"""Type variable for enum member values."""


class DeprecatedMemberWarning(DeprecationWarning):
    """Warning category for deprecated enum members."""


class DeprecatedMember:
    """Class to mark members as deprecated.

    This class should not be used directly, use
    [`deprecated_member`][frequenz.core.enum.deprecated_member] instead.

    Please read the [`Enum`][frequenz.core.enum.Enum] documentation for details and
    examples.
    """

    # Using slots is just an optimization to make the class more lightweight and avoid
    # the creation of a `__dict__` for each instance and its corresponding lookup.
    __slots__ = ("value", "message", "new_name", "since")

    # One overload with `message` and one with only `new_name`, so a call with
    # neither matches none of them.
    @overload
    def __init__(  # noqa: D107
        self,
        value: Any,
        message: str,
        *,
        new_name: str | None = None,
        since: str | None = None,
    ) -> None: ...

    @overload
    def __init__(  # noqa: D107
        self,
        value: Any,
        message: None = None,
        *,
        new_name: str,
        since: str | None = None,
    ) -> None: ...

    def __init__(  # noqa: DOC502
        self,
        value: Any,
        message: str | None = None,
        *,
        new_name: str | None = None,
        since: str | None = None,
    ) -> None:
        """Initialize this instance.

        At least one of `message` and `new_name` must be given.

        Args:
            value: The value of the enum member to mark as deprecated.
            message: The warning message to emit when the member is reached, or
                `None` to generate it from `new_name`.
            new_name: The name of the member to use instead, in the same enum.
            since: The version the member is deprecated since, such as `"v1.2.0"`,
                for the documentation only.

        Raises:
            TypeError: If neither `message` nor `new_name` is given, or if
                `new_name` or `since` is not a string.
            ValueError: If `new_name` is not an identifier, or if `since` is empty.
        """
        self.value: Any = value
        """The value of the deprecated member."""

        self.message: str | None = message
        """The warning message, or `None` if it is generated from `new_name`.

        A generated message is only known once the enum class is created, since it
        includes the class' fully qualified name, and is not stored here.
        """

        self.new_name: str | None = new_name
        """The name of the member to use instead, in the same enum, if given."""

        self.since: str | None = since
        """The version the member is deprecated since, if given.

        It is only used for the documentation, never in the warning.
        """

        self._validate()

    def _validate(self) -> None:
        """Check the fields.

        `message` is not checked, as it never was before `new_name` and `since`
        were added, so existing code passing something else keeps working.

        Raises:
            TypeError: If neither `message` nor `new_name` is given, or if
                `new_name` or `since` is not a string.
            ValueError: If `new_name` is not an identifier, or if `since` is empty.
        """
        if self.message is None and self.new_name is None:
            raise TypeError(
                "a deprecated member needs message, new_name or both, got neither"
            )
        if self.new_name is not None:
            if not isinstance(self.new_name, str):
                raise TypeError(f"new_name must be a str, got {self.new_name!r}")
            if not self.new_name.isidentifier():
                raise ValueError(
                    f"new_name must be an identifier, got {self.new_name!r}"
                )
        if self.since is not None:
            if not isinstance(self.since, str):
                raise TypeError(f"since must be a str, got {self.since!r}")
            if not self.since.strip():
                raise ValueError("since must not be empty")


@overload
def deprecated_member(
    value: ValueT,
    message: str,
    *,
    new_name: str | None = None,
    since: str | None = None,
) -> ValueT: ...


@overload
def deprecated_member(
    value: ValueT,
    message: None = None,
    *,
    new_name: str,
    since: str | None = None,
) -> ValueT: ...


def deprecated_member(  # noqa: DOC502
    value: ValueT,
    message: str | None = None,
    *,
    new_name: str | None = None,
    since: str | None = None,
) -> ValueT:
    """Mark an enum member as deprecated.

    At least one of `message` and `new_name` must be given. With `new_name` alone,
    reaching the member warns with `<Enum>.<NAME> is deprecated. Use
    <Enum>.<new_name> instead.`, with fully qualified names, which is what the
    deprecations guide asks for. `message` replaces that warning.

    `since` is not part of the warning: it is only there for the documentation.
    [`griffe-frequenz-core`](https://github.com/frequenz-floss/griffe-frequenz-core)
    reads it, together with `new_name`, to generate the member's `Deprecated:`
    notice, so `message` changes the warning only. To change the notice, write a
    `Deprecated:` admonition by hand in the member's docstring, which replaces the
    generated one.

    When the enum class is created, `new_name` is checked to be another member of
    the same enum, which is not deprecated itself.

    Please read the [`Enum`][frequenz.core.enum.Enum] documentation for details and
    examples.

    Args:
        value: The value of the enum member to mark as deprecated.
        message: The warning message to emit when the member is reached, or `None`
            to generate it from `new_name`.
        new_name: The name of the member to use instead, in the same enum.
        since: The version the member is deprecated since, such as `"v1.2.0"`, for
            the documentation only.

    Returns:
        The wrapped value, to mark the enum member as deprecated.

    Raises:
        TypeError: If neither `message` nor `new_name` is given, or if `new_name`
            or `since` is not a string.
        ValueError: If `new_name` is not an identifier, or if `since` is empty.
    """
    # The overloads of `deprecated_member()` already checked the combination, which
    # mypy can't tell from the `| None` types here.
    member = DeprecatedMember(
        value, message, new_name=new_name, since=since  # type: ignore[arg-type]
    )
    return cast(ValueT, member)


def _deprecation_messages(
    cls: type[enum.Enum], deprecated: Mapping[str, DeprecatedMember]
) -> dict[str, str]:
    """Return the warning message of each deprecated member of a new enum class.

    Args:
        cls: The enum class just created.
        deprecated: The deprecated members of `cls`, by name.

    Returns:
        The warning message for each name in `deprecated`: its own `message`, or
            one generated from its `new_name`.

    Raises:
        ValueError: If a `new_name` is not a member of `cls`, or is deprecated
            itself.
    """
    prefix = f"{cls.__module__}.{cls.__qualname__}"
    messages: dict[str, str] = {}
    for name, member in deprecated.items():
        if member.new_name is not None:
            if member.new_name not in cls.__members__:
                raise ValueError(
                    f"the new_name of {prefix}.{name} is not a member of "
                    f"{prefix}: {member.new_name!r}"
                )
            if member.new_name in deprecated:
                raise ValueError(
                    f"the new_name of {prefix}.{name} is {member.new_name!r}, "
                    "which is deprecated too"
                )
        if member.message is not None:
            messages[name] = member.message
        else:
            messages[name] = (
                f"{prefix}.{name} is deprecated. Use {prefix}.{member.new_name} "
                "instead."
            )
    return messages


class DeprecatingEnumType(enum.EnumType):
    """Enum metaclass that supports deprecated members.

    Tip:
        Normally it is not necessary to use this class directly, use
        [`Enum`][frequenz.core.enum.Enum] instead.

    Behavior:

    - In the class body, members may be declared as
      `NAME = deprecated_member(value, ...)`. See
      [`deprecated_member()`][frequenz.core.enum.deprecated_member] and
      [`DeprecatedMember`][frequenz.core.enum.DeprecatedMember] for details.
    - During class creation, these wrappers are replaced with `value` so that
      a normal enum member or alias is created by [`EnumType`][enum.EnumType].
    - Once the class is created, each `new_name` is checked to be a member that is
      not deprecated, and the warnings of members without a `message` are
      generated from it, now that the fully qualified name of the class is known.
    - The deprecated names are recorded so that:

        * `MyEnum.NAME` warns (attribute access by name)
        * `MyEnum["NAME"]` warns (lookup by name)
        * `MyEnum(value)` warns **only if** the resolved member has **no**
            non-deprecated aliases (all names for that member are deprecated).
    """

    def __new__(  # pylint: disable=too-many-locals
        mcs,
        name: str,
        bases: tuple[type[EnumT], ...],
        classdict: Mapping[str, Any],
        **kw: Any,
    ) -> type[EnumT]:
        """Create the new enum class rewriting deprecated members.

        Members declared as
        [`DeprecatedMember`][frequenz.core.enum.DeprecatedMember] are replaced
        with their value.
        """
        deprecated: dict[str, DeprecatedMember] = {}
        prepared = super().__prepare__(name, bases, **kw)

        # Unwrap DeprecatedMembers and record them as deprecated
        for key, value in classdict.items():
            if isinstance(value, DeprecatedMember):
                deprecated[key] = value
                prepared[key] = value.value
            else:
                prepared[key] = value

        cls = cast(type[EnumT], super().__new__(mcs, name, bases, prepared, **kw))
        deprecated_names = _deprecation_messages(cls, deprecated)

        # Build alias groups: member -> list of names
        member_to_names: dict[EnumT, list[str]] = {}
        member: EnumT
        for member_name, member in cls.__members__.items():
            member_to_names.setdefault(member, []).append(member_name)

        warned_by_member: dict[EnumT, str] = {}
        for member, names in member_to_names.items():
            # warn on value only if all alias names are deprecated
            deprecated_aliases = [n for n in names if n in deprecated_names]
            if deprecated_aliases and len(deprecated_aliases) == len(names):
                warned_by_member[member] = deprecated_names[deprecated_aliases[0]]

        # Inject maps quietly
        type.__setattr__(cls, "__deprecated_names__", deprecated_names)
        type.__setattr__(cls, "__deprecated_value_map__", warned_by_member)

        return cls

    @staticmethod
    def _name_map(cls_: type[Any]) -> Mapping[str, str]:
        """Map from member names to deprecation messages."""
        return cast(
            Mapping[str, str],
            type.__getattribute__(cls_, "__dict__").get("__deprecated_names__", {}),
        )

    @staticmethod
    def _value_map(cls_: type[Any]) -> Mapping[Any, str]:
        """Map from enum members to deprecation messages."""
        return cast(
            Mapping[Any, str],
            type.__getattribute__(cls_, "__dict__").get("__deprecated_value_map__", {}),
        )

    def __getattribute__(cls, name: str) -> Any:
        """Resolve `name` to a member, warning if the member is deprecated."""
        if name in ("__deprecated_names__", "__deprecated_value_map__"):
            return type.__getattribute__(cls, name)
        deprecated = DeprecatingEnumType._name_map(cls)
        if name in deprecated:
            warnings.warn(deprecated[name], DeprecatedMemberWarning, stacklevel=2)
        return super().__getattribute__(name)

    def __getitem__(cls, name: str) -> Any:
        """Resolve `name` to a member, warning if the member is deprecated."""
        deprecated = DeprecatingEnumType._name_map(cls)
        if name in deprecated:
            warnings.warn(deprecated[name], DeprecatedMemberWarning, stacklevel=2)
        return super().__getitem__(name)

    def __call__(cls, value: Any, *args: Any, **kwargs: Any) -> Any:
        """Resolve `value` to a member, warning if the member is purely deprecated."""
        member = super().__call__(value, *args, **kwargs)
        value_map: Mapping[Any, str] = DeprecatingEnumType._value_map(cls)
        msg = value_map.get(member)
        if msg is not None:
            warnings.warn(msg, DeprecatedMemberWarning, stacklevel=2)
        return member


if TYPE_CHECKING:
    # Make type checkers treat it as a plain Enum (so member checks work), if we don't
    # do this, mypy will consider the resulting enum completely dynamic and never
    # complain if an unexisting member is accessed.

    # pylint: disable-next=missing-class-docstring
    class Enum(enum.Enum):  # noqa
        __deprecated_names__: ClassVar[Mapping[str, str]]
        __deprecated_value_map__: ClassVar[Mapping[Enum, str]]

else:

    class Enum(enum.Enum, metaclass=DeprecatingEnumType):
        """Base class for enums that support deprecated members.

        This class extends the standard library's [`enum.Enum`][] to support marking
        certain members as deprecated. Deprecated members can be accessed, but doing so
        will emit a [`DeprecationWarning`][], specifically
        a [`DeprecatedMemberWarning`][frequenz.core.enum.DeprecatedMemberWarning].

        To declare a deprecated member, use the
        [`deprecated_member()`][frequenz.core.enum.deprecated_member] function.

        When using the enum constructor (i.e. `MyEnum(value)`), a warning is only emitted if
        the resolved member has no non-deprecated aliases. If there is at least one
        non-deprecated alias for the member, no warning is emitted.

        Example:
            ```python
            from frequenz.core.enum import Enum, deprecated_member

            class TaskStatus(Enum):
                OPEN = 1
                IN_PROGRESS = 2
                FINISHED = 3
                PENDING = deprecated_member(1, new_name="OPEN", since="v1.2.0")
                CANCELLED = deprecated_member(
                    4,
                    "mypkg.TaskStatus.CANCELLED is deprecated. "
                    "Cancelled tasks are deleted now.",
                    since="v1.3.0",
                )

            # Accessing deprecated members by name warns:
            status1 = TaskStatus.PENDING
            assert status1 is TaskStatus.OPEN

            status2 = TaskStatus["PENDING"]
            assert status2 is TaskStatus.OPEN

            # No warning, 1 resolves to OPEN, which is not deprecated
            status3 = TaskStatus(1)
            assert status3 is TaskStatus.OPEN

            # Warns, as all the names for 4 are deprecated
            status4 = TaskStatus(4)
            assert status4.name == "CANCELLED"
            ```

            `PENDING` is a plain rename, so `new_name` is enough: reaching it warns
            with `mypkg.TaskStatus.PENDING is deprecated. Use
            mypkg.TaskStatus.OPEN instead.`, `mypkg` being the module defining
            the enum, and
            [`griffe-frequenz-core`](https://github.com/frequenz-floss/griffe-frequenz-core)
            documents it with a ``Deprecated since v1.2.0. Use
            [`OPEN`][mypkg.TaskStatus.OPEN] instead.`` notice.

            `CANCELLED` has no member to point at, so it gives its own `message`,
            starting with its fully qualified name. That replaces the warning
            only, so its notice is written by hand, as a `Deprecated:` admonition
            in the member's docstring.
        """

        __deprecated_names__: ClassVar[Mapping[str, str]]
        __deprecated_value_map__: ClassVar[Mapping[Self, str]]


def unique(enumeration: type[EnumT]) -> type[EnumT]:
    """Class decorator for enums that ensures unique non-deprecated values.

    This works similarly to [`@enum.unique`][enum.unique], but it only enforces
    uniqueness for members that are not deprecated. This allows deprecated members to
    be aliases for non-deprecated members without causing a `ValueError`.

    If you need strict uniqueness for all deprecated and non-deprecated members, use
    [`@enum.unique`][enum.unique] instead.

    Example:
        ```python
        from frequenz.core.enum import Enum, deprecated_member, unique

        @unique
        class TaskStatus(Enum):
            OPEN = 1
            IN_PROGRESS = 2
            # This is okay, as PENDING is a deprecated alias.
            PENDING = deprecated_member(1, new_name="OPEN", since="v1.2.0")
        ```

    Args:
        enumeration: The enum class to decorate.

    Returns:
        The decorated enum class.

    Raises:
        ValueError: If duplicate values are found among non-deprecated members.
    """
    # Retrieve the map of deprecated names created by the metaclass.
    deprecated_names = enumeration.__dict__.get("__deprecated_names__", {})

    duplicates = []
    seen_values: dict[Any, str] = {}
    for member_name, member in enumeration.__members__.items():
        # Ignore members that are marked as deprecated.
        if member_name in deprecated_names:
            continue

        value = member.value
        if value in seen_values:
            duplicates.append((member_name, seen_values[value]))
        else:
            seen_values[value] = member_name

    if duplicates:
        alias_details = ", ".join(
            f"{name!r} -> {alias!r}" for name, alias in duplicates
        )
        raise ValueError(
            f"duplicate values found in {enumeration.__name__}: {alias_details}"
        )

    return enumeration
