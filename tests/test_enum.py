# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Tests for the `frequenz.core.enum` module."""

import pytest

from frequenz.core.enum import DeprecatedMember, DeprecatedMemberWarning, Enum, unique


class _TestEnum(Enum):
    """A test enum with some deprecated members."""

    OPEN = 1
    IN_PROGRESS = 2
    PENDING = DeprecatedMember(1, "Use OPEN instead")
    DONE = DeprecatedMember(3, "Use FINISHED instead")
    FINISHED = 4


def _assert_deprecated_member(
    recorder: pytest.WarningsRecorder, expected_msg: str
) -> None:
    """Assert that a single deprecation warning was recorded with the expected message."""
    assert len(recorder.list) == 1
    warning = recorder.pop().message
    assert str(warning) == expected_msg
    assert isinstance(warning, DeprecatedMemberWarning)


def test_mypy_detects_deprecated_members() -> None:
    """Test that mypy detects missing members as expected.

    If mypy wouldn't detect this, it should complain about an unused type: ignore.
    """
    with pytest.raises(AttributeError):
        _ = _TestEnum.I_DONT_EXIST  # type: ignore[attr-defined]


def test_attribute_access_warns() -> None:
    """Test accessing deprecated members as attributes triggers a deprecation warning."""
    with pytest.deprecated_call() as recorder:
        _ = _TestEnum.PENDING
    _assert_deprecated_member(recorder, "Use OPEN instead")

    with pytest.deprecated_call() as recorder:
        _ = _TestEnum.DONE
    _assert_deprecated_member(recorder, "Use FINISHED instead")


def test_name_lookup_warns() -> None:
    """Test accessing deprecated members by name triggers a deprecation warning."""
    with pytest.deprecated_call() as recorder:
        _ = _TestEnum["PENDING"]
    _assert_deprecated_member(recorder, "Use OPEN instead")

    with pytest.deprecated_call() as recorder:
        _ = _TestEnum["DONE"]
    _assert_deprecated_member(recorder, "Use FINISHED instead")


def test_value_lookup_behavior_non_deprecated_alias() -> None:
    """Test accessing members by value triggers no warnings when a non-deprecated alias exists."""
    member = _TestEnum(1)
    assert member is _TestEnum.OPEN


def test_value_lookup_behavior_purely_deprecated() -> None:
    """Test accessing members by value triggers warnings when there is no non-deprecated alias."""
    with pytest.deprecated_call() as recorder:
        member = _TestEnum(3)
    _assert_deprecated_member(recorder, "Use FINISHED instead")
    with pytest.deprecated_call():  # Avoid pytest showing the deprecation in the output
        assert member is _TestEnum.DONE


def test_members_integrity() -> None:
    """Test that all enum members are present in __members__."""
    names = list(_TestEnum.__members__.keys())
    assert {"OPEN", "IN_PROGRESS", "PENDING", "DONE", "FINISHED"} <= set(names)


def test_unique_decorator_success_with_deprecated_alias() -> None:
    """Test that `unique` allows deprecated members to be aliases."""

    @unique
    class _Status(Enum):
        """An enum with a deprecated alias that should pass the unique check."""

        ACTIVE = 1
        INACTIVE = 2
        PENDING = DeprecatedMember(1, "Use ACTIVE instead")

    with pytest.deprecated_call():
        assert _Status.PENDING is _Status.ACTIVE  # type: ignore[comparison-overlap]


def test_unique_decorator_fail_on_non_deprecated_duplicates() -> None:
    """Test that `unique` raises ValueError for duplicates among non-deprecated members."""
    with pytest.raises(ValueError) as execinfo:

        @unique
        class _Status(Enum):
            """An enum with a non-deprecated duplicate value."""

            ACTIVE = 1
            INACTIVE = 2
            DUPLICATE_ACTIVE = 1

    error_msg = str(execinfo.value)
    assert "duplicate values found" in error_msg
    assert "'DUPLICATE_ACTIVE' -> 'ACTIVE'" in error_msg


def test_unique_decorator_fail_on_multiple_duplicates() -> None:
    """Test that `unique` reports all non-deprecated duplicate values."""
    with pytest.raises(ValueError) as execinfo:

        @unique
        class _Status(Enum):
            """An enum with multiple non-deprecated duplicate values."""

            A = 1
            B = 2
            C = 1  # Duplicate of A
            D = 2  # Duplicate of B
            E = 3

    error_msg = str(execinfo.value)
    assert "duplicate values found" in error_msg
    assert "'C' -> 'A'" in error_msg
    assert "'D' -> 'B'" in error_msg


def test_unique_decorator_success_simple() -> None:
    """Test that `unique` works correctly on a simple enum with no duplicates."""

    @unique
    class _Status(Enum):
        """A simple unique enum."""

        A = 1
        B = 2

    # The test passes if no ValueError is raised.
    assert len(_Status) == 2


def test_unique_decorator_success_empty_enum() -> None:
    """Test that `unique` works correctly on an empty enum."""

    @unique
    class _EmptyStatus(Enum):
        """An empty enum."""

    assert len(_EmptyStatus) == 0


def test_unique_decorator_success_all_deprecated() -> None:
    """Test `unique` when all members are deprecated, with some being aliases."""

    @unique
    class _AllDeprecated(Enum):
        """An enum where all members are deprecated."""

        OLD_A = DeprecatedMember(1, "Use something else")
        OLD_B = DeprecatedMember(1, "Also use something else")

    with pytest.deprecated_call():
        assert _AllDeprecated.OLD_A is _AllDeprecated.OLD_B  # type: ignore[comparison-overlap]
