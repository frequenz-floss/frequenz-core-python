# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Tests for the `frequenz.core.enum` module."""

import pytest

from frequenz.core.enum import (
    DeprecatedMember,
    DeprecatedMemberWarning,
    Enum,
)


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
