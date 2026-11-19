# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Deprecating module-level symbols that can't take a `@deprecated` decorator.

See the package documentation for the background.
"""

import importlib
import string
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import Any, overload

from typing_extensions import deprecated


@dataclass(frozen=True, init=False, slots=True)
class DeprecatedAlias:
    """A symbol kept reachable from its old name.

    Each one is an entry for
    [`deprecated_symbols`][frequenz.core.warnings.deprecated_symbols], which has the
    examples.

    The symbol moved to another module, `new_module`, was renamed, `new_name`, or
    both. Without `new_module` it is still in the module defining the alias, under
    its new name.

    Reaching the alias warns with `<old> is deprecated. Use <new> instead.`, with
    fully qualified names, following the Frequenz deprecation guide, or with
    `message` if something else is needed.

    `since`, the version the alias is deprecated since, is not part of the
    warning: it is only there for the documentation.
    [`griffe-frequenz-core`](https://github.com/frequenz-floss/griffe-frequenz-core)
    reads it, together with where the symbol is now, to generate the alias'
    `Deprecated:` notice, so `message` changes the warning only. To change the
    notice, write a `Deprecated:` admonition by hand in the docstring of the alias
    declared for type checkers, which replaces the generated one.

    Everything is checked when the alias is created rather than when it is
    reached.
    """

    name: str
    """The deprecated name, in the module defining the alias."""

    new_module: str | None
    """The fully qualified name of the module the symbol lives in now.

    `None` if it is still in the module defining the alias, under
    [`new_name`][frequenz.core.warnings.DeprecatedAlias.new_name].
    """

    new_name: str
    """The name the symbol has now.

    The same as [`name`][frequenz.core.warnings.DeprecatedAlias.name] if it was not
    renamed.
    """

    since: str | None
    """The version the alias is deprecated since, or `None` if not given.

    It is only used for the documentation, never in the warning.
    """

    message: str | None
    """The template for the warning message, or `None` for the standard one.

    It is formatted with `{old}` and `{new}`, the fully qualified names of the
    alias and of the symbol it resolves to, as plain fields, without attributes,
    indexes, conversions or format specs.
    """

    # One overload with `new_module` and one with only `new_name`, so a call with
    # neither matches none of them.
    @overload
    def __init__(  # noqa: D107
        self,
        name: str,
        /,
        *,
        new_module: str,
        new_name: str | None = None,
        since: str | None = None,
        message: str | None = None,
    ) -> None: ...

    @overload
    def __init__(  # noqa: D107
        self,
        name: str,
        /,
        *,
        new_module: None = None,
        new_name: str,
        since: str | None = None,
        message: str | None = None,
    ) -> None: ...

    def __init__(  # noqa: DOC502
        self,
        name: str,
        /,
        *,
        new_module: str | None = None,
        new_name: str | None = None,
        since: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize this instance.

        At least one of `new_module` and `new_name` must be given.

        Args:
            name: The deprecated name, in the module defining the alias.
            new_module: The fully qualified name of the module the symbol lives in
                now, if it moved out of the module defining the alias.
            new_name: The name the symbol has now, if it was renamed.
            since: The version the alias is deprecated since, such as `"v1.2.0"`,
                for the documentation only.
            message: The template for the warning message, replacing the standard
                `<old> is deprecated. Use <new> instead.`, formatted with `{old}`
                and `{new}`, the fully qualified names of the alias and of the
                symbol it resolves to, as plain fields, without attributes,
                indexes, conversions or format specs.

        Raises:
            TypeError: If an argument is not a string, or if neither `new_module`
                nor `new_name` is given.
            ValueError: If `name`, `new_name` or a part of `new_module` is not an
                identifier, if `since` is empty, or if `message` is not a template
                with only plain `{old}` and `{new}` fields.
        """
        # The class is frozen, which blocks plain assignment here too.
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "new_module", new_module)
        object.__setattr__(self, "new_name", name if new_name is None else new_name)
        object.__setattr__(self, "since", since)
        object.__setattr__(self, "message", message)
        self._validate(new_name)

    def _resolve(self, module: str) -> tuple[Any, str]:
        """Look up the target before formatting the warning.

        Args:
            module: The module that defines the alias.

        Returns:
            The target object and the warning text.

        Raises:
            TypeError: If the target is a module.
        """
        new_module = module if self.new_module is None else self.new_module
        new = f"{new_module}.{self.new_name}"
        value = getattr(importlib.import_module(new_module), self.new_name)
        if isinstance(value, ModuleType):
            raise TypeError(
                f"the target of {module}.{self.name} is the module {new}, and this "
                "aliases names, not modules: the import system never consults a "
                f"package's __getattr__, so `import {module}.{self.name}` would fail "
                f"anyway. Keep a real __init__.py at {module}.{self.name}, with the "
                "aliases for the names it used to hold in it."
            )
        return value, self.format_message(old=f"{module}.{self.name}", new=new)

    def format_message(self, *, old: str, new: str) -> str:
        """Format the warning message for this alias.

        Args:
            old: The fully qualified name of the alias.
            new: The fully qualified name of the symbol it resolves to.

        Returns:
            The alias' `message` formatted with `old` and `new`, or
                `<old> is deprecated. Use <new> instead.` if it has none.
        """
        if self.message is None:
            return f"{old} is deprecated. Use {new} instead."
        return self.message.format(old=old, new=new)

    def _validate(self, new_name: str | None) -> None:
        """Check the fields.

        Args:
            new_name: The `new_name` given to `__init__()`, before it defaulted to
                `name`, to tell whether it was given at all.

        Raises:
            TypeError: If neither `new_module` nor `new_name` is given.
        """
        if self.new_module is None and new_name is None:
            raise TypeError(
                f"the alias {self.name!r} needs new_module, new_name or both, "
                "got neither"
            )
        _check_name("alias", self.name)
        if self.new_module is not None:
            _check_dotted_name(
                self.name, "new_module", self.new_module, "a module name"
            )
        self._validate_new_name()
        _check_since(self.name, self.since)
        _check_message(self.name, self.message, ("old", "new"))

    def _validate_new_name(self) -> None:
        """Check that `new_name` is an identifier.

        Raises:
            TypeError: If it is not a string.
            ValueError: If it is not an identifier.
        """
        if not isinstance(self.new_name, str):
            raise TypeError(
                f"the new_name of {self.name!r} must be a str, got {self.new_name!r}"
            )
        if not self.new_name.isidentifier():
            raise ValueError(
                f"the new_name of {self.name!r} is not an identifier: "
                f"{self.new_name!r}"
            )


@dataclass(frozen=True, init=False, slots=True)
class DeprecatedSymbol:
    """A deprecated module attribute and the value it still returns.

    Pass this entry to [`deprecated_symbols`][frequenz.core.warnings.deprecated_symbols]
    to deprecate a constant, type variable or type alias. These cannot take the
    [`typing_extensions.deprecated`][] decorator. If the same object is still
    available under another name or in another module, use a
    [`DeprecatedAlias`][frequenz.core.warnings.DeprecatedAlias] instead.

    Declare the deprecated name only for type checkers. Python calls the module's
    `__getattr__` only when an attribute is missing. It then returns `value`.

    The default warning is `<old> is deprecated. Use <replacement> instead.`
    Both names are fully qualified. Without a replacement, the warning is just
    `<old> is deprecated.` In that case, provide a `message` that tells callers
    what to do.

    Use `since` to record the version that deprecated the symbol. The runtime
    warning does not include this version. Use `message` to customize the warning.

    To show a deprecation notice in your API docs, use
    [`griffe-frequenz-core`](https://github.com/frequenz-floss/griffe-frequenz-core).
    If the symbol has no `replacement`, write a `Deprecated:` notice in the
    symbol’s docstring under `if TYPE_CHECKING:`.

    Everything is checked when the entry is created rather than when it is
    reached.
    """

    name: str
    """The deprecated name, in the module defining the symbol."""

    value: Any
    """The object returned when someone uses the deprecated name."""

    replacement: str | None
    """The fully qualified name of what to use instead, or `None` if there is none.

    It is only used in the messages: unlike a
    [`DeprecatedAlias`][frequenz.core.warnings.DeprecatedAlias], the symbol is not
    the same object as its replacement.
    """

    since: str | None
    """The version the symbol is deprecated since, or `None` if not given.

    It is only used for the documentation, never in the warning.
    """

    message: str | None
    """The template for the warning message, or `None` for the standard one.

    It is formatted with `{old}`, the fully qualified name of the symbol, and
    `{new}`, its [`replacement`][frequenz.core.warnings.DeprecatedSymbol.replacement]
    if it has one, as plain fields, without attributes, indexes, conversions or
    format specs.
    """

    def __init__(  # noqa: DOC502
        self,
        name: str,
        /,
        *,
        value: Any,
        replacement: str | None = None,
        since: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize this instance.

        Args:
            name: The deprecated name, in the module defining the symbol.
            value: The object the deprecated name gives.
            replacement: The fully qualified name of what to use instead, if there
                is something.
            since: The version the symbol is deprecated since, such as `"v1.2.0"`,
                for the documentation only.
            message: The template for the warning message, replacing the standard
                one, formatted with `{old}`, the fully qualified name of the
                symbol, and `{new}`, its `replacement` if it has one, as plain
                fields, without attributes, indexes, conversions or format specs.

        Raises:
            TypeError: If an argument is not a string.
            ValueError: If `name` or a part of `replacement` is not an identifier,
                if `since` is empty, or if `message` is not a template with only a
                plain `{old}` field, and a plain `{new}` one if there is a
                `replacement`.
        """
        # The class is frozen, which blocks plain assignment here too.
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "replacement", replacement)
        object.__setattr__(self, "since", since)
        object.__setattr__(self, "message", message)
        self._validate()

    def _resolve(self, module: str) -> tuple[Any, str]:
        """Return the stored value and warning text.

        Args:
            module: The module that defines the symbol.

        Returns:
            The stored value and the warning text.
        """
        return self.value, self.format_message(old=f"{module}.{self.name}")

    def format_message(self, *, old: str) -> str:
        """Format the warning message for this symbol.

        Args:
            old: The fully qualified name of the symbol.

        Returns:
            The symbol's `message` formatted with `old` and its `replacement`, or
                `<old> is deprecated. Use <replacement> instead.` if it has no
                `message`, or `<old> is deprecated.` if it has neither.
        """
        if self.message is not None:
            if self.replacement is None:
                return self.message.format(old=old)
            return self.message.format(old=old, new=self.replacement)
        if self.replacement is None:
            return f"{old} is deprecated."
        return f"{old} is deprecated. Use {self.replacement} instead."

    def _validate(self) -> None:
        """Check the fields."""
        _check_name("symbol", self.name)
        if self.replacement is not None:
            _check_dotted_name(
                self.name, "replacement", self.replacement, "a fully qualified name"
            )
        _check_since(self.name, self.since)
        _check_message(
            self.name,
            self.message,
            ("old",) if self.replacement is None else ("old", "new"),
        )


def deprecated_symbols(  # noqa: DOC502
    module: str,
    /,
    *symbols: DeprecatedAlias | DeprecatedSymbol,
    category: type[Warning] = DeprecationWarning,
    stacklevel: int = 2,
) -> Callable[[str], Any]:
    '''Build a module `__getattr__` that warns about deprecated symbols.

    Use this for module-level symbols that should keep working, but warn whoever
    uses them, when a [`typing_extensions.deprecated`][] decorator is not an
    option. There are two kinds, and a module can have both in the same call:

    - A [`DeprecatedAlias`][frequenz.core.warnings.DeprecatedAlias] keeps the old
      import path of a symbol that moved to another module, or was renamed. The
      decorator is not an option because the object is not yours to mark:
      decorating it would deprecate it for everybody, including the users of its
      new home or name. The alias stays the very same object, so
      [`isinstance`][] keeps working through both paths.
    - A [`DeprecatedSymbol`][frequenz.core.warnings.DeprecatedSymbol] is a symbol
      deprecated where it is, that the decorator can't mark because it is not a
      class or a function, such as a type variable, a constant or a type alias.

    Each entry says since which version it is deprecated, so symbols deprecated in
    different releases are documented with their own version, and can give their
    own warning message.

    Danger:
        Follow the usage example structure strictly. In particular never drop
        the `else:`, otherwise a type checker will see the `__getattr__`
        assignment and treat every symbol in the module as [`Any`][typing.Any],
        effectively disabling type checking for the entire module.

    Warning: Star imports
        A star import (`from module import *`) only consults `__getattr__` for
        the names listed in the module's `__all__`. Without an `__all__`, it
        takes only the names the module defines itself, so the deprecated symbols
        silently disappear from star imports, and code using them fails with a
        [`NameError`][] instead of getting the deprecation warning. Keep every
        deprecated symbol in `__all__` until it is removed.

    Example: Usage
        This is how a module that used to define `Decimal` itself, and now gets it
        from [`decimal`][], keeps the old import path working:

        ```python
        from typing import TYPE_CHECKING, TypeAlias

        from frequenz.core.warnings import DeprecatedAlias, deprecated_symbols

        __all__ = ["Decimal"]  # Keeps the alias in star imports

        if TYPE_CHECKING:
            # Private import, only for type checkers
            from decimal import Decimal as _Decimal

            Decimal: TypeAlias = _Decimal
        else:
            __getattr__ = deprecated_symbols(
                __name__,
                DeprecatedAlias("Decimal", new_module="decimal", since="v1.2.0"),
            )
        ```

        Reaching `Decimal` through this module, say `mypkg.Decimal`, now emits a
        `DeprecationWarning` saying `mypkg.Decimal is deprecated. Use
        decimal.Decimal instead.`

        `since` doesn't change the warning: it is for
        [`griffe-frequenz-core`](https://github.com/frequenz-floss/griffe-frequenz-core),
        which documents the alias with a ``Deprecated since v1.2.0. Use
        [`decimal.Decimal`][] instead.`` notice.

    Example: Renaming
        When the symbol was also renamed on the way out, `new_name` gives the name
        it has now:

        ```python
        from typing import TYPE_CHECKING, TypeAlias

        from frequenz.core.warnings import DeprecatedAlias, deprecated_symbols

        if TYPE_CHECKING:
            from fractions import Fraction as _Fraction

            Rational: TypeAlias = _Fraction
        else:
            __getattr__ = deprecated_symbols(
                __name__,
                DeprecatedAlias(
                    "Rational",
                    new_module="fractions",
                    new_name="Fraction",
                    since="v1.3.0",
                ),
            )
        ```

        Without `new_module`, the symbol was renamed in this very module:

        ```python
        from typing import TYPE_CHECKING, TypeAlias

        from frequenz.core.warnings import DeprecatedAlias, deprecated_symbols


        class Widget:
            ...  # Called Gadget before v1.4.0


        if TYPE_CHECKING:
            Gadget: TypeAlias = Widget
        else:
            __getattr__ = deprecated_symbols(
                __name__,
                DeprecatedAlias("Gadget", new_name="Widget", since="v1.4.0"),
            )
        ```

    Example: Custom message
        When the standard warning is not enough, an alias can give its own
        message, as a template that gets the fully qualified old and new names as
        `{old}` and `{new}`:

        ```python
        from typing import TYPE_CHECKING, TypeAlias

        from frequenz.core.warnings import DeprecatedAlias, deprecated_symbols

        if TYPE_CHECKING:
            from decimal import Decimal as _Decimal

            Decimal: TypeAlias = _Decimal
        else:
            __getattr__ = deprecated_symbols(
                __name__,
                DeprecatedAlias(
                    "Decimal",
                    new_module="decimal",
                    since="v1.2.0",
                    message="{old} is deprecated and will be removed in v2.0.0. "
                    "Use {new} instead.",
                ),
            )
        ```

        The message replaces the warning only: the notice is still generated from
        `since` and where the symbol is now. To say more in the documentation too,
        write a `Deprecated:` admonition by hand in the docstring of `Decimal` in
        the `if TYPE_CHECKING:` branch, which replaces the generated notice.

    Example: Deprecating in place
        A symbol that is not moving, but is replaced by something else, such as a
        constant in seconds replaced by a [`timedelta`][datetime.timedelta], is a
        [`DeprecatedSymbol`][frequenz.core.warnings.DeprecatedSymbol]. The
        `__getattr__` is only called for names the module doesn't have, so the
        value is kept under a private name, given to the entry as `value`, and the
        public name is only declared for type checkers:

        ```python
        from datetime import timedelta
        from typing import TYPE_CHECKING, Final

        from frequenz.core.warnings import DeprecatedSymbol, deprecated_symbols

        __all__ = ["TIMEOUT", "TIMEOUT_SECONDS"]

        TIMEOUT: Final = timedelta(seconds=30)
        """How long to wait for a reply."""

        _TIMEOUT_SECONDS: Final = 30.0

        if TYPE_CHECKING:
            TIMEOUT_SECONDS: Final = _TIMEOUT_SECONDS
            """How long to wait for a reply, in seconds."""
        else:
            __getattr__ = deprecated_symbols(
                __name__,
                DeprecatedSymbol(
                    "TIMEOUT_SECONDS",
                    value=_TIMEOUT_SECONDS,
                    replacement="mypkg.TIMEOUT",
                    since="v1.5.0",
                ),
            )
        ```

        Reaching `mypkg.TIMEOUT_SECONDS` now gives `30.0` and emits a
        `DeprecationWarning` saying `mypkg.TIMEOUT_SECONDS is deprecated. Use
        mypkg.TIMEOUT instead.` `replacement` is a fully qualified name, used only
        in the messages, since `TIMEOUT` is not the same object.

        Without a `replacement`, the symbol is just going away. The warning would
        only say `<old> is deprecated.`, so give a `message` saying what to do
        instead, and write the notice by hand:

        ```python
        from typing import TYPE_CHECKING, TypeVar

        from frequenz.core.warnings import DeprecatedSymbol, deprecated_symbols

        __all__ = ["ValueT"]

        if TYPE_CHECKING:
            ValueT = TypeVar("ValueT")
            """A type variable for values.

            Deprecated:
                Deprecated since v1.6.0. Define your own type variable instead.
            """
        else:
            __getattr__ = deprecated_symbols(
                __name__,
                DeprecatedSymbol(
                    "ValueT",
                    value=TypeVar("ValueT"),
                    since="v1.6.0",
                    message="{old} is deprecated and will be removed in v2.0.0. "
                    "Define your own type variable instead.",
                ),
            )
        ```

    Tip: Deprecating whole modules
        This function can't be used to deprecate a whole module. If you need to
        do that, you can keep a real `__init__.py` at the old path, with a
        `__getattr__ = deprecated_symbols(...)` that includes all the symbols
        that used to be reachable there.

    Warning: Security Warning
        This function imports the modules the aliases point at, so the aliases are
        as trusted as an `import` statement in this module. Write them out as
        literals; don't build them from anything that comes from outside the
        program.

    Args:
        module: The fully qualified name of the module defining the symbols.
        *symbols: The deprecated symbols, at least one, each with its own name.
        category: The category of the warning to emit.
        stacklevel: How far up the stack the warning is reported, counting from the
            `__getattr__` itself. The default of 2 points at the code reaching for
            the symbol, and only needs raising if something wraps the returned
            function.

    Returns:
        A function suitable for use as the module's `__getattr__`.

    Raises:
        TypeError: If an argument has the wrong type, including an entry that is
            neither a [`DeprecatedAlias`][frequenz.core.warnings.DeprecatedAlias]
            nor a [`DeprecatedSymbol`][frequenz.core.warnings.DeprecatedSymbol], or
            a `DeprecatedSymbol` whose value is a module. Also later, when an alias
            is reached, if it resolves to a module rather than to a symbol in one.
        ValueError: If there are no symbols, if two of them have the same name, if
            an alias points at a deprecated symbol in the same module, itself
            included, or if `stacklevel` is smaller than 1.
    '''
    if not isinstance(module, str):
        raise TypeError(f"module must be a str, got {module!r}")
    if not (isinstance(category, type) and issubclass(category, Warning)):
        raise TypeError(f"category must be a Warning subclass, got {category!r}")
    if not isinstance(stacklevel, int):
        raise TypeError(f"stacklevel must be an int, got {stacklevel!r}")
    if stacklevel < 1:
        raise ValueError(f"stacklevel must be 1 or more, got {stacklevel!r}")
    by_name = _checked_symbols(module, symbols)

    def module_getattr(name: str) -> Any:  # noqa: DOC503
        """Return a deprecated symbol, warning about it.

        Args:
            name: The name being looked up in the module.

        Returns:
            The object the deprecated symbol gives.

        Raises:
            AttributeError: If the name is not one of the deprecated symbols.
            TypeError: If an alias resolves to a module, which this can't keep
                reachable from its old path.
        """
        entry = by_name.get(name)
        if entry is None:
            raise AttributeError(f"module {module!r} has no attribute {name!r}")
        value, message = entry._resolve(module)  # pylint: disable=protected-access
        warnings.warn(message, category, stacklevel=stacklevel)
        return value

    return module_getattr


def _checked_symbols(
    module: str, symbols: tuple[DeprecatedAlias | DeprecatedSymbol, ...]
) -> dict[str, DeprecatedAlias | DeprecatedSymbol]:
    """Check the entries given to `deprecated_symbols()` as a whole.

    Each entry checks its own fields when it is created; this checks what only
    the whole table can tell.

    Args:
        module: The fully qualified name of the module defining the symbols.
        symbols: The entries.

    Returns:
        The entries by name.

    Raises:
        TypeError: If an entry is neither a `DeprecatedAlias` nor a
            `DeprecatedSymbol`, or if a `DeprecatedSymbol`'s value is a module.
        ValueError: If there are no entries, if two of them have the same name, or
            if an alias points at a deprecated symbol in the same module.
    """
    if not symbols:
        raise ValueError(f"no deprecated symbols given for module {module!r}")
    by_name: dict[str, DeprecatedAlias | DeprecatedSymbol] = {}
    for entry in symbols:
        # Also what a mapping, the form `deprecated_aliases()` used to take, runs
        # into.
        if not isinstance(entry, (DeprecatedAlias, DeprecatedSymbol)):
            raise TypeError(
                "deprecated symbols must be DeprecatedAlias or DeprecatedSymbol "
                f"instances, got {entry!r}"
            )
        # A dict literal would keep the last of two entries silently; this is the
        # one place that can tell.
        if entry.name in by_name:
            raise ValueError(f"the symbol {entry.name!r} is given more than once")
        if isinstance(entry, DeprecatedSymbol) and isinstance(entry.value, ModuleType):
            raise TypeError(
                f"the value of {module}.{entry.name} is the module "
                f"{entry.value.__name__}, and this deprecates names, not modules: "
                "the import system never consults a package's __getattr__, so "
                f"`import {module}.{entry.name}` would fail anyway. Keep a real "
                f"__init__.py at {module}.{entry.name}, with the deprecated names "
                "it used to hold in it."
            )
        by_name[entry.name] = entry
    for entry in symbols:
        # Reaching it would call this `__getattr__` again, and never stop if the
        # aliases point at each other. Pointing at a `DeprecatedSymbol` wouldn't
        # loop, but would warn twice and send users to something deprecated too.
        if (
            isinstance(entry, DeprecatedAlias)
            and entry.new_module in (None, module)
            and entry.new_name in by_name
        ):
            raise ValueError(
                f"the alias {entry.name!r} points at {module}.{entry.new_name}, "
                "which is deprecated too"
            )
    return by_name


@deprecated(
    "frequenz.core.warnings.deprecated_aliases is deprecated. "
    "Use frequenz.core.warnings.deprecated_symbols instead."
)
def deprecated_aliases(  # noqa: DOC502
    module: str,
    /,
    *aliases: DeprecatedAlias,
    category: type[Warning] = DeprecationWarning,
    stacklevel: int = 2,
) -> Callable[[str], Any]:
    """Build a module `__getattr__` that warns about deprecated aliases.

    Deprecated:
        Deprecated since v1.7.0. Use
        [`deprecated_symbols`][frequenz.core.warnings.deprecated_symbols]
        with the same arguments. The old function will be removed in v2.0.0.

    Args:
        module: The fully qualified name of the module defining the aliases.
        *aliases: The deprecated aliases, at least one, each with its own name.
        category: The category of the warning to emit.
        stacklevel: How far up the stack the warning is reported, counting from the
            `__getattr__` itself.

    Returns:
        A function suitable for use as the module's `__getattr__`.

    Raises:
        TypeError: If an argument has the wrong type.
        ValueError: If the aliases are not valid together, or if `stacklevel` is
            smaller than 1.
    """
    return deprecated_symbols(
        module, *aliases, category=category, stacklevel=stacklevel
    )


def _check_name(kind: str, name: object) -> None:
    """Check that the entry has a valid Python identifier.

    Args:
        kind: The entry type to show in error messages.
        name: The name to check.

    Raises:
        TypeError: If it is not a string.
        ValueError: If it is not an identifier.
    """
    if not isinstance(name, str):
        raise TypeError(f"{kind} names must be str, got {name!r}")
    if not name.isidentifier():
        raise ValueError(f"{kind} names must be identifiers, got {name!r}")


def _check_dotted_name(name: str, field: str, value: object, what: str) -> None:
    """Check that each part of a dotted name is an identifier.

    Args:
        name: The name of the entry, for the error messages.
        field: The name of the field, for the error messages.
        value: The value of the field.
        what: What the field should be, for the error messages.

    Raises:
        TypeError: If it is not a string.
        ValueError: If one of its dotted parts is not an identifier.
    """
    if not isinstance(value, str):
        raise TypeError(f"the {field} of {name!r} must be a str, got {value!r}")
    if not all(part.isidentifier() for part in value.split(".")):
        raise ValueError(f"the {field} of {name!r} is not {what}: {value!r}")


def _check_since(name: str, since: object) -> None:
    """Check that `since` is a nonempty string or `None`.

    Args:
        name: The name of the entry, for the error messages.
        since: The `since` to check.

    Raises:
        TypeError: If it is not a string.
        ValueError: If it is empty or blank.
    """
    if since is None:
        return
    if not isinstance(since, str):
        raise TypeError(f"the since of {name!r} must be a str, got {since!r}")
    if not since.strip():
        raise ValueError(f"the since of {name!r} is empty")


def _check_message(name: str, message: object, fields: tuple[str, ...]) -> None:
    """Check that a warning template uses only the allowed plain fields.

    Args:
        name: The name of the entry, for the error messages.
        message: The `message` to check.
        fields: The names of the fields it may use.

    Raises:
        TypeError: If it is not a string.
        ValueError: If it has a stray brace, or a replacement field other than one
            of `fields`, plain.
    """
    if message is None:
        return
    if not isinstance(message, str):
        raise TypeError(f"the message of {name!r} must be a str, got {message!r}")
    allowed = " and ".join(f"{{{field}}}" for field in fields)
    problem = (
        f"the message of {name!r} must be a template with only plain {allowed} "
        f"fields, got {message!r}"
    )
    try:
        # A stray brace raises here.
        parsed = list(string.Formatter().parse(message))
    except ValueError as error:
        raise ValueError(problem) from error
    # Anything more than a plain field can fail depending on the names it is
    # formatted with, which are only known when the entry is reached, so
    # formatting it once here can't tell: `{old.missing}` raises
    # `AttributeError`, and `{old:{new}}` makes the new name a format spec.
    if not all(
        (field is None or field in fields) and not spec and conversion is None
        for _, field, spec, conversion in parsed
    ):
        raise ValueError(problem)
