# Frequenz Core Library Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

- [`Interval`][frequenz.core.math.Interval]'s type parameter no longer includes `None`. The exported type variable `LessThanComparableOrNoneT` (bound to `LessThanComparable | None`) was deprecated and replaced with `LessThanComparableT` (bound to `LessThanComparable`). `None` is still accepted as a value for `start` / `end` to indicate an unbounded side, but it is treated purely as bound metadata rather than a value in the interval's comparable space.

  Migration:

  - `Interval[int | None]` → `Interval[int]`
  - `Interval[LessThanComparable | None]` → `Interval[LessThanComparable]`
  - `LessThanComparableOrNoneT` (importable name) → `LessThanComparableT`

  Note that explicitly using `Interval[int | None]` still works, as `(int | None) | None` is equivalent to `int | None`, even when it is no longer needed nor recommended. Old code will mostly work, but there is one soft breaking change: `None in some_interval` and `None in some_interval_set` is now a type-check error at call sites, matching the design intent that `None` is a bound marker and never a member value.

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
