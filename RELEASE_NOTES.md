# Frequenz Core Library Release Notes

## Summary

This release updates the `Interval` type to no longer include `None` in its type parameter, and introduces a new `IntervalSet` type to the `frequenz.core.math` module, which allows for efficient membership testing of normalized sets of intervals.

## Upgrading

- [`Interval`][frequenz.core.math.Interval]'s type parameter no longer includes `None`. The exported type variable `LessThanComparableOrNoneT` (bound to `LessThanComparable | None`) was deprecated and replaced with `LessThanComparableT` (bound to `LessThanComparable`). `None` is still accepted as a value for `start` / `end` to indicate an unbounded side, but it is treated purely as bound metadata rather than a value in the interval's comparable space.

  Migration:

  - `Interval[int | None]` → `Interval[int]`
  - `Interval[LessThanComparable | None]` → `Interval[LessThanComparable]`
  - `LessThanComparableOrNoneT` (importable name) → `LessThanComparableT`

  Note that explicitly using `Interval[int | None]` still works, as `(int | None) | None` is equivalent to `int | None`, even when it is no longer needed nor recommended. Old code will mostly work, but there is one soft breaking change: `None in some_interval` and `None in some_interval_set` is now a type-check error at call sites, matching the design intent that `None` is a bound marker and never a member value.

## New Features

- Add [`IntervalSet`][frequenz.core.math.IntervalSet] to [`frequenz.core.math`][frequenz.core.math], a normalized set of [`Interval`][frequenz.core.math.Interval] values with `O(log n)` membership testing.

  Overlapping or touching intervals are merged on construction, and `None` bounds (`-∞` / `+∞`) are handled during merging.

  Useful for allow/forbid-list style checks that previously required iterating a `Sequence[Interval]`:

  ```python
  from frequenz.core.math import Interval, IntervalSet

  allowed = IntervalSet(
      (Interval(1, 5), Interval(3, 10), Interval(15, 20))
  )
  assert tuple(allowed) == (Interval(1, 10), Interval(15, 20))
  assert 7 in allowed
  assert 12 not in allowed
  ```
