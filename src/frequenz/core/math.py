# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Math tools."""

import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Generic, Protocol, Self, TypeVar

from .typing import FloatInt


def is_close_to_zero(value: FloatInt, abs_tol: FloatInt = 1e-9) -> bool:
    """Check if a floating point value is close to zero.

    A value of 1e-9 is a commonly used absolute tolerance to balance precision
    and robustness for floating-point numbers comparisons close to zero. Note
    that this is also the default value for the relative tolerance.
    For more technical details, see https://peps.python.org/pep-0485/#behavior-near-zero

    Args:
        value: The floating point value to compare to.
        abs_tol: The minimum absolute tolerance. Defaults to 1e-9.

    Returns:
        Whether the floating point value is close to zero.
    """
    zero: float = 0.0
    return math.isclose(a=value, b=zero, abs_tol=abs_tol)


class LessThanComparable(Protocol):
    """A protocol that requires the `__lt__` method to compare values."""

    def __lt__(self, other: Self, /) -> bool:
        """Return whether self is less than other."""


LessThanComparableT = TypeVar("LessThanComparableT", bound=LessThanComparable)
"""Type variable for a value that is [`LessThanComparable`][..LessThanComparable]."""


LessThanComparableOrNoneT = TypeVar(
    "LessThanComparableOrNoneT", bound=LessThanComparable | None
)
"""Type variable for a value that is [`LessThanComparable`][..LessThanComparable] or `None`.

Warning: Deprecated
    This type variable is deprecated and it will be removed in a future version. Use
    [`LessThanComparableT`][..LessThanComparableT] instead.
"""


@dataclass(frozen=True, repr=False)
class Interval(Generic[LessThanComparableT]):
    """An interval to test if a value is within its limits.

    The [`.start`][.start] and [`.end`][.end] are inclusive, meaning that the
    [`.start`][.start] and [`.end`][.end] limits are included in the range when
    checking if a value is contained by the interval.

    If the [`.start`][.start] or [`.end`][.end] is `None`, it means that the interval
    is unbounded in that direction. `None` is used purely as a bound marker; it is
    never a value in the interval.

    If [`.start`][.start] is bigger than [`.end`][.end], a `ValueError` is raised.

    The type stored in the interval must be comparable, meaning that it must implement
    the `__lt__` method to be able to compare values.
    """

    start: LessThanComparableT | None
    """The start of the interval, or `None` to indicate no lower bound (-∞)."""

    end: LessThanComparableT | None
    """The end of the interval, or `None` to indicate no upper bound (+∞)."""

    def __post_init__(self) -> None:
        """Check if the start is less than or equal to the end."""
        if self.start is None or self.end is None:
            return
        if self.start > self.end:
            raise ValueError(
                f"The start ({self.start}) can't be bigger than end ({self.end})"
            )

    def __contains__(self, item: LessThanComparableT) -> bool:
        """Check if the value is within the range of the interval.

        Args:
            item: The value to check.

        Returns:
            True if value is within the range, otherwise False.
        """
        if self.start is not None and item < self.start:
            return False
        if self.end is not None and item > self.end:
            return False
        return True

    def __repr__(self) -> str:
        """Return a string representation of this instance."""
        return f"Interval({self.start!r}, {self.end!r})"

    def __str__(self) -> str:
        """Return a string representation of this instance."""
        start = "∞" if self.start is None else str(self.start)
        end = "∞" if self.end is None else str(self.end)
        return f"[{start}, {end}]"


@dataclass(frozen=True, repr=False)
class IntervalSet(Generic[LessThanComparableT]):
    """A normalized set of intervals for efficient membership testing.

    An [`IntervalSet`][.] represents the union of a collection of
    [`Interval`][..Interval] values. On construction, the passed intervals are sorted
    by their start and any overlapping or touching intervals are merged into one, so
    the stored [`.intervals`][.] are canonical: sorted by start and pairwise
    non-overlapping.

    Membership testing via the `in` operator is `O(log n)` on the number of stored
    intervals (after normalization), using binary search on the interval starts.

    Only the normalized form is stored; the original input order and any redundant
    intervals are discarded. Two [`IntervalSet`][.] instances constructed from
    different input sequences that represent the same union of values are equal and
    hash the same.

    Note: Unbounded intervals
        [`Interval`][..Interval] supports `None` as the start (meaning -∞) or the end
        (meaning +∞). [`IntervalSet`][.] handles these correctly during merging: for
        example, the set `{Interval(None, 5), Interval(3, None)}` normalizes to
        `{Interval(None, None)}` (the whole comparable space). `None` is a bound
        marker only; it is never a value in the set.

    Example:
        ```python
        from frequenz.core.math import Interval, IntervalSet

        allowed = IntervalSet(
            (Interval(1, 5), Interval(3, 10), Interval(15, 20))
        )
        assert tuple(allowed) == (Interval(1, 10), Interval(15, 20))
        assert 7 in allowed
        assert 12 not in allowed
        ```
    """

    intervals: tuple[Interval[LessThanComparableT], ...] = ()
    """The normalized intervals in this set: sorted by start and non-overlapping."""

    def __post_init__(self) -> None:
        """Normalize the passed intervals by sorting and merging overlapping ones."""
        object.__setattr__(self, "intervals", _sort_and_merge(self.intervals))

    def __contains__(self, item: LessThanComparableT) -> bool:
        """Check whether the value is within any interval of this set.

        Args:
            item: The value to check.

        Returns:
            Whether `item` is within any interval of this set.
        """
        if not self.intervals:
            return False

        # Binary search for the rightmost interval whose start is `<= item`. A `None`
        # start means -∞, which is always `<= item`.
        lo, hi = 0, len(self.intervals)
        while lo < hi:
            mid = (lo + hi) // 2
            start = self.intervals[mid].start
            if start is None or not item < start:
                lo = mid + 1
            else:
                hi = mid

        idx = lo - 1
        return idx >= 0 and item in self.intervals[idx]

    def __iter__(self) -> Iterator[Interval[LessThanComparableT]]:
        """Iterate over the normalized intervals in ascending order of start."""
        return iter(self.intervals)

    def __len__(self) -> int:
        """Return the number of intervals in the normalized form."""
        return len(self.intervals)

    def __repr__(self) -> str:
        """Return a string representation of this instance."""
        return f"IntervalSet({self.intervals!r})"

    def __str__(self) -> str:
        """Return a string representation of this instance."""
        if not self.intervals:
            return "∅"
        return " ∪ ".join(str(iv) for iv in self.intervals)


def _sort_and_merge(
    intervals: Iterable[Interval[LessThanComparableT]],
) -> tuple[Interval[LessThanComparableT], ...]:
    """Sort intervals by start and merge overlapping or touching ones.

    A `None` start is treated as -∞ and a `None` end as +∞. Intervals are inclusive
    on both bounds, so `[1, 5]` and `[5, 10]` are considered touching and merged
    into `[1, 10]`.

    Args:
        intervals: The intervals to normalize.

    Returns:
        A tuple of sorted, pairwise non-overlapping intervals covering the same
            values as the input.
    """
    all_ivs = list(intervals)
    if not all_ivs:
        return ()

    # Left-unbounded intervals (start is None) can't be sorted alongside real starts,
    # so pre-merge them into at most one interval spanning -∞ up to the largest end.
    # Pair the real-start intervals with their (narrowed) non-None start so the sort
    # key is directly typed as `T` — no casts needed.
    with_none_start: list[Interval[LessThanComparableT]] = []
    with_real_start: list[tuple[LessThanComparableT, Interval[LessThanComparableT]]] = (
        []
    )
    for iv in all_ivs:
        if iv.start is None:
            with_none_start.append(iv)
        else:
            with_real_start.append((iv.start, iv))

    with_real_start.sort(key=lambda pair: pair[0])
    ordered_real = [pair[1] for pair in with_real_start]

    initial: list[Interval[LessThanComparableT]] = []
    if with_none_start:
        if any(iv.end is None for iv in with_none_start):
            initial.append(Interval(None, None))
        else:
            non_none_ends = [iv.end for iv in with_none_start if iv.end is not None]
            initial.append(Interval(None, max(non_none_ends)))

    ordered = initial + ordered_real

    result: list[Interval[LessThanComparableT]] = [ordered[0]]
    for current in ordered[1:]:
        last = result[-1]
        if _end_covers_start(last.end, current.start):
            new_end = _max_end(last.end, current.end)
            result[-1] = Interval(last.start, new_end)
        else:
            result.append(current)

    return tuple(result)


def _end_covers_start(
    end_val: LessThanComparableT | None,
    start_val: LessThanComparableT | None,
) -> bool:
    """Return whether `end_val >= start_val`, treating `None` as ±∞.

    Args:
        end_val: An interval end, where `None` means +∞.
        start_val: An interval start, where `None` means -∞.

    Returns:
        Whether `end_val >= start_val` under the ±∞ convention.
    """
    if end_val is None:
        return True
    if start_val is None:
        return True
    return not end_val < start_val


def _max_end(
    a: LessThanComparableT | None,
    b: LessThanComparableT | None,
) -> LessThanComparableT | None:
    """Return the larger of two interval ends, where `None` means +∞.

    Args:
        a: An interval end.
        b: Another interval end.

    Returns:
        The larger of `a` and `b` under the +∞ convention.
    """
    if a is None or b is None:
        return None
    return b if a < b else a
