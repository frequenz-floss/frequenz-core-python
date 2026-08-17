# Frequenz Core Library Release Notes

## Upgrading

- [`Interval`][frequenz.core.math.Interval]'s type parameter no longer includes `None`. The exported type variable `LessThanComparableOrNoneT` (bound to `LessThanComparable | None`) was deprecated and replaced with `LessThanComparableT` (bound to `LessThanComparable`). `None` is still accepted as a value for `start` / `end` to indicate an unbounded side, but it is treated purely as bound metadata rather than a value in the interval's comparable space.

  Migration:

  - `Interval[int | None]` → `Interval[int]`
  - `Interval[LessThanComparable | None]` → `Interval[LessThanComparable]`
  - `LessThanComparableOrNoneT` (importable name) → `LessThanComparableT`

  Note that explicitly using `Interval[int | None]` still works, as `(int | None) | None` is equivalent to `int | None`, even when it is no longer needed nor recommended. Old code will mostly work, but there is one soft breaking change: `None in some_interval` and `None in some_interval_set` is now a type-check error at call sites, matching the design intent that `None` is a bound marker and never a member value.

## New Features

- Added [`FloatInt`][frequenz.core.typing.FloatInt], a type alias for `float | int`.

  [PEP 484](https://peps.python.org/pep-0484/)'s [numeric tower](https://peps.python.org/pep-0484/#the-numeric-tower) makes `int` assignable wherever `float` is annotated, while at runtime `isinstance(1, float)` is `False`. A plain `float` annotation therefore silently admits values that break `match … case float():` arms and `float`-only methods like `hex()`.

  Annotate with `FloatInt` instead of a plain `float`: the alias docstring documents the trap in detail, including the inherent `bool ⊂ int` leak.

- [`is_close_to_zero()`][frequenz.core.math.is_close_to_zero] now annotates its `value` and `abs_tol` parameters as [`FloatInt`][frequenz.core.typing.FloatInt]. This is a pure widening, `int` arguments were always accepted by type checkers, the annotation just didn't admit it.
