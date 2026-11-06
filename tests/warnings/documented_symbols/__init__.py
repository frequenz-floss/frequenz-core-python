# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""A package written the way `deprecated_symbols()` documents, for the tests.

The other tests build a `ModuleType` and assign the `__getattr__` onto it, which
exercises the function but not the shape the docstring tells people to write: the
symbols declared under `if TYPE_CHECKING:`, the assignment in the `else:` branch,
and a real module the import system loads. This package is that shape, so the
tests importing from here fail if the documented pattern stops working.
"""

from datetime import timedelta
from typing import TYPE_CHECKING, Final, TypeAlias, TypeVar

from frequenz.core.warnings import DeprecatedAlias, DeprecatedSymbol, deprecated_symbols

__all__ = ["TIMEOUT", "TIMEOUT_SECONDS", "Decimal", "Rational", "ValueT", "kept"]

TIMEOUT: Final = timedelta(seconds=30)
"""How long to wait for a reply."""

_TIMEOUT_SECONDS: Final = 30.0

if TYPE_CHECKING:
    # Only for type checkers, which can't see the runtime `__getattr__` in the
    # `else` branch.
    from decimal import Decimal as _Decimal
    from fractions import Fraction as _Fraction

    Decimal: TypeAlias = _Decimal
    """A decimal number."""

    Rational: TypeAlias = _Fraction
    """A rational number.

    Deprecated:
        Deprecated since v1.3.0, and will be removed in v2.0.0. Use
        [`fractions.Fraction`][] instead.
    """

    TIMEOUT_SECONDS: Final = _TIMEOUT_SECONDS
    """How long to wait for a reply, in seconds."""

    ValueT = TypeVar("ValueT")
    """A type variable for values.

    Deprecated:
        Deprecated since v1.6.0. Define your own type variable instead.
    """
else:
    __getattr__ = deprecated_symbols(
        __name__,
        DeprecatedAlias("Decimal", new_module="decimal", since="v1.2.0"),
        DeprecatedAlias(
            "Rational",
            new_module="fractions",
            new_name="Fraction",
            since="v1.3.0",
            message="{old} is deprecated and will be removed in v2.0.0. "
            "Use {new} instead.",
        ),
        DeprecatedSymbol(
            "TIMEOUT_SECONDS",
            value=_TIMEOUT_SECONDS,
            replacement="tests.warnings.documented_symbols.TIMEOUT",
            since="v1.5.0",
        ),
        DeprecatedSymbol(
            "ValueT",
            value=TypeVar("ValueT"),
            since="v1.6.0",
            message="{old} is deprecated and will be removed in v2.0.0. "
            "Define your own type variable instead.",
        ),
    )


def kept() -> str:
    """Return the name of a symbol this package still defines itself."""
    return "kept"
