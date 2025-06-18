# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Tests for IDs."""

from typing import final

import pytest

from frequenz.core.id import BaseId


@final
class _TestId(BaseId, str_prefix="TEST_ID"):
    """A test ID class that inherits from BaseId."""


@final
class _TestId2(BaseId, str_prefix="TEST_ID2", allow_custom_name=True):
    """Another test ID class that inherits from BaseId."""


def test_valid() -> None:
    """Test creating a valid ID."""
    id_obj = _TestId(42)
    assert int(id_obj) == 42


def test_warn_non_unique_prefix() -> None:
    """Test that using a non-unique prefix raises a warning."""
    with pytest.warns(UserWarning, match="Prefix 'TEST_ID' is already registered"):

        class _TestDuplicateId(BaseId, str_prefix="TEST_ID"):
            """A duplicate test ID class with the same prefix as _TestId."""

        _TestDuplicateId(1)


def test_negative_raises() -> None:
    """Test that creating a negative ID raises ValueError."""
    with pytest.raises(ValueError, match="_TestId can't be negative"):
        _TestId(-1)


def test_equality() -> None:
    """Test equality comparison."""
    assert _TestId(1) == _TestId(1)
    assert _TestId(1) != _TestId(2)
    assert _TestId(1) != _TestId2(1)


def test_ordering() -> None:
    """Test ordering comparison."""
    assert _TestId(1) < _TestId(2)
    # Not unnecessary as BaseId only provides the __lt__ method
    assert not _TestId(2) < _TestId(1)  # pylint: disable=unnecessary-negation

    # Test against other types
    with pytest.raises(TypeError):
        _ = _TestId(1) < _TestId2(2)


def test_hash() -> None:
    """Test hash behavior."""
    # Same IDs should hash to same value
    assert hash(_TestId(1)) == hash(_TestId(1))
    # Different IDs should hash to different values
    assert hash(_TestId(1)) != hash(_TestId(2))

    # Same ID but different types should hash to different values
    # (note this test might be flaky, as a hash collision could occur)
    assert hash(_TestId(1)) != hash(_TestId2(1))


def test_str_and_repr() -> None:
    """Test string representations."""
    id_obj = _TestId(42)
    assert str(id_obj) == "TEST_ID42"
    assert repr(id_obj) == "_TestId(42)"
