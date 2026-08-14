# License: MIT
# Copyright © 2026 Frequenz Energy-as-a-Service GmbH

"""Tests for the `IntervalSet` class."""

import pytest

from frequenz.core.math import Interval, IntervalSet


def test_empty_default() -> None:
    """An `IntervalSet` built with no arguments is empty and contains nothing."""
    interval_set: IntervalSet[int] = IntervalSet()
    assert len(interval_set) == 0
    assert not list(interval_set)
    assert 0 not in interval_set


def test_empty_explicit_tuple() -> None:
    """An `IntervalSet` built from an empty tuple is empty."""
    interval_set: IntervalSet[int] = IntervalSet(())
    assert len(interval_set) == 0
    assert not list(interval_set)


def test_single_interval() -> None:
    """A single interval is stored as-is and its inclusive bounds are respected."""
    interval_set = IntervalSet((Interval(1, 5),))
    assert list(interval_set) == [Interval(1, 5)]
    assert 3 in interval_set
    assert 1 in interval_set
    assert 5 in interval_set
    assert 0 not in interval_set
    assert 6 not in interval_set


def test_overlap_merged() -> None:
    """Overlapping intervals collapse into their union."""
    interval_set = IntervalSet((Interval(1, 5), Interval(3, 10)))
    assert list(interval_set) == [Interval(1, 10)]
    assert 7 in interval_set
    assert 12 not in interval_set


def test_containment_merged() -> None:
    """A fully-contained interval is absorbed by the larger one."""
    interval_set = IntervalSet((Interval(1, 5), Interval(2, 4)))
    assert list(interval_set) == [Interval(1, 5)]


def test_touching_intervals_merged() -> None:
    """Intervals sharing an inclusive endpoint are considered overlapping."""
    interval_set = IntervalSet((Interval(1, 5), Interval(5, 10)))
    assert list(interval_set) == [Interval(1, 10)]


def test_disjoint_intervals_kept() -> None:
    """Non-overlapping intervals remain separate."""
    interval_set = IntervalSet((Interval(1, 5), Interval(10, 20)))
    assert list(interval_set) == [Interval(1, 5), Interval(10, 20)]
    assert 3 in interval_set
    assert 7 not in interval_set
    assert 15 in interval_set
    assert 25 not in interval_set


def test_input_order_ignored() -> None:
    """Construction is independent of input order."""
    forward = IntervalSet((Interval(1, 5), Interval(10, 20)))
    reversed_input = IntervalSet((Interval(10, 20), Interval(1, 5)))
    assert forward == reversed_input
    assert list(forward) == list(reversed_input)


def test_duplicates_collapsed() -> None:
    """Duplicate intervals collapse into one."""
    interval_set = IntervalSet((Interval(1, 5), Interval(1, 5), Interval(1, 5)))
    assert list(interval_set) == [Interval(1, 5)]


def test_chain_of_overlaps_merged() -> None:
    """A chain of overlapping intervals collapses into a single interval."""
    interval_set = IntervalSet(
        (Interval(1, 3), Interval(2, 5), Interval(4, 7), Interval(6, 9))
    )
    assert list(interval_set) == [Interval(1, 9)]


def test_unbounded_start() -> None:
    """A left-unbounded interval contains everything up to its end."""
    interval_set: IntervalSet[int] = IntervalSet((Interval(None, 5),))
    assert -1000 in interval_set
    assert 3 in interval_set
    assert 5 in interval_set
    assert 6 not in interval_set


def test_unbounded_end() -> None:
    """A right-unbounded interval contains everything from its start onward."""
    interval_set: IntervalSet[int] = IntervalSet((Interval(5, None),))
    assert 5 in interval_set
    assert 1000 in interval_set
    assert 4 not in interval_set


def test_fully_unbounded_contains_every_value() -> None:
    """A fully-unbounded interval contains every value in the comparable space."""
    interval_set: IntervalSet[int] = IntervalSet((Interval(None, None),))
    assert 0 in interval_set
    assert -1000 in interval_set
    assert 1000 in interval_set


def test_merge_with_unbounded_start() -> None:
    """A left-unbounded interval absorbs anything it touches on the right."""
    interval_set: IntervalSet[int] = IntervalSet((Interval(None, 5), Interval(3, 10)))
    assert list(interval_set) == [Interval(None, 10)]


def test_merge_with_unbounded_end() -> None:
    """A right-unbounded interval absorbs anything it touches on the left."""
    interval_set: IntervalSet[int] = IntervalSet((Interval(5, None), Interval(3, 10)))
    assert list(interval_set) == [Interval(3, None)]


def test_merge_covers_whole_space() -> None:
    """Two overlapping half-unbounded intervals collapse to the whole space."""
    interval_set: IntervalSet[int] = IntervalSet((Interval(None, 5), Interval(3, None)))
    assert list(interval_set) == [Interval(None, None)]


def test_multiple_unbounded_starts_pick_max_end() -> None:
    """Multiple left-unbounded intervals merge into one ending at the max end."""
    interval_set: IntervalSet[int] = IntervalSet(
        (Interval(None, 3), Interval(None, 5), Interval(None, 1))
    )
    assert list(interval_set) == [Interval(None, 5)]


def test_multiple_unbounded_ends_pick_min_start() -> None:
    """Multiple right-unbounded intervals merge into one starting at the min start."""
    interval_set: IntervalSet[int] = IntervalSet(
        (Interval(5, None), Interval(3, None), Interval(7, None))
    )
    assert list(interval_set) == [Interval(3, None)]


def test_unbounded_start_swallows_all() -> None:
    """A fully-unbounded interval swallows every other interval."""
    interval_set: IntervalSet[int] = IntervalSet(
        (Interval(None, None), Interval(3, 5), Interval(10, 20))
    )
    assert list(interval_set) == [Interval(None, None)]


def test_equality_by_normalized_form() -> None:
    """Two sets with the same normalized form are equal."""
    left = IntervalSet((Interval(1, 5), Interval(10, 20)))
    right = IntervalSet(
        (Interval(19, 20), Interval(10, 19), Interval(1, 3), Interval(2, 5))
    )
    assert left == right


def test_hashable_when_bounds_are_hashable() -> None:
    """`IntervalSet` values with hashable bounds are hashable and equal-hash."""
    left = IntervalSet((Interval(1, 5), Interval(10, 20)))
    right = IntervalSet((Interval(10, 20), Interval(1, 5)))
    assert hash(left) == hash(right)
    assert {left, right} == {left}


def test_repr_shows_normalized_intervals() -> None:
    """`repr()` shows the class name and the normalized intervals."""
    interval_set = IntervalSet((Interval(3, 10), Interval(1, 5)))
    rendered = repr(interval_set)
    assert rendered == "IntervalSet((Interval(1, 10),))"


def test_str_empty() -> None:
    """`str()` of an empty set is `∅`."""
    interval_set: IntervalSet[int] = IntervalSet()
    assert str(interval_set) == "∅"


def test_str_uses_union_notation() -> None:
    """`str()` of a non-empty set joins interval `str()`s with ` ∪ `."""
    interval_set = IntervalSet((Interval(1, 5), Interval(10, 20)))
    assert str(interval_set) == "[1, 5] ∪ [10, 20]"


def test_str_unbounded_uses_infinity() -> None:
    """`str()` of a fully-unbounded set uses the infinity symbols from `Interval`."""
    interval_set: IntervalSet[int] = IntervalSet((Interval(None, None),))
    assert str(interval_set) == "[∞, ∞]"


def test_binary_search_across_many_intervals() -> None:
    """Membership works correctly across many disjoint intervals."""
    interval_set = IntervalSet(
        (
            Interval(0, 10),
            Interval(20, 30),
            Interval(40, 50),
            Interval(60, 70),
            Interval(80, 90),
        )
    )
    assert 5 in interval_set
    assert 25 in interval_set
    assert 45 in interval_set
    assert 65 in interval_set
    assert 85 in interval_set
    assert 15 not in interval_set
    assert 35 not in interval_set
    assert 55 not in interval_set
    assert 75 not in interval_set
    assert -1 not in interval_set
    assert 100 not in interval_set


def test_iter_returns_normalized_order() -> None:
    """Iteration yields intervals sorted by start."""
    interval_set = IntervalSet((Interval(30, 40), Interval(1, 5), Interval(10, 20)))
    assert list(interval_set) == [
        Interval(1, 5),
        Interval(10, 20),
        Interval(30, 40),
    ]


def test_float_bounds() -> None:
    """Works with `float` bounds."""
    interval_set = IntervalSet((Interval(1.0, 5.5), Interval(3.2, 10.7)))
    assert list(interval_set) == [Interval(1.0, 10.7)]
    assert 4.5 in interval_set
    assert 11.0 not in interval_set


def test_covariance() -> None:
    """Test that `IntervalSet` is covariant in its value type.

    This is a type-level check: assigning an `IntervalSet[bool]` to an
    `IntervalSet[int]` (`bool` is a subtype of `int`) only passes the type checker if
    `IntervalSet` is covariant; with an invariant type parameter `mypy` would reject
    it. At runtime the assignment is a no-op, so the actual verification is done by
    `mypy`.
    """
    narrower: IntervalSet[bool] = IntervalSet((Interval(False, True),))
    wider: IntervalSet[int] = narrower
    assert wider is narrower


@pytest.mark.parametrize("incomparable", ["a string", None, object()])
def test_contains_incomparable_type_raises(incomparable: object) -> None:
    """Test that checking membership of an incomparable value raises `TypeError`.

    `__contains__` accepts any `object` (so `IntervalSet` can be covariant), but a
    value whose type is not compatible with the set's value type must fail loudly at
    runtime with a clear error rather than silently returning a result or a cryptic
    comparison error.
    """
    interval_set = IntervalSet((Interval(1, 5),))
    with pytest.raises(TypeError, match=r"is not compatible with this set's value"):
        _ = incomparable in interval_set
