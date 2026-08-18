# Frequenz Core Library Release Notes

## Summary

This release updates the `Interval` type to no longer include `None` in its type parameter, and introduces a new `IntervalSet` type to the `frequenz.core.math` module, which allows for efficient membership testing of normalized sets of intervals.

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

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
