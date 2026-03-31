# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Tests for the log module."""

import pytest

from frequenz.core.module import get_public_module_name


@pytest.mark.parametrize(
    "module_name, expected_logger_name",
    [
        ("some.pub", "some.pub"),
        ("some.pub._some._priv", "some.pub"),
        ("some.pub._some._priv.public", "some.pub"),
        ("some.pub._some._priv.public._private", "some.pub"),
        ("some._priv.pub", "some"),
        ("_priv.some.pub", None),
        ("some", "some"),
        ("some._priv", "some"),
        ("_priv", None),
    ],
)
def test_get_public_logger(module_name: str, expected_logger_name: str | None) -> None:
    """Test that the logger name is as expected."""
    name = get_public_module_name(module_name)
    assert name == expected_logger_name
