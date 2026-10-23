# License: MIT
# Copyright © 2025 Frequenz Energy-as-a-Service GmbH

"""Tests for the `frequenz.core.enum` module."""

from typing import Any

import pytest

from frequenz.core.enum import (
    DeprecatedMember,
    DeprecatedMemberWarning,
    Enum,
    deprecated_member,
    unique,
)


class _TestEnum(Enum):
    """A test enum with some deprecated members."""

    OPEN = 1
    IN_PROGRESS = 2
    PENDING = deprecated_member(1, "Use OPEN instead")
    DONE = deprecated_member(3, "Use FINISHED instead")
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


def test_mypy_deprecated_member_correct_value_type() -> None:
    """Test that mypy sees the correct value type for deprecated members.

    If mypy wouldn't detect this, it should complain about value not having the
    correct type.
    """
    _: int = _TestEnum.PENDING.value


def test_deprecated_member_helper_returns_wrapper() -> None:
    """Test the helper returns a DeprecatedMember wrapper preserving metadata."""
    wrapper = deprecated_member(123, "Value 123 is deprecated")
    assert isinstance(wrapper, DeprecatedMember)
    assert wrapper.value == 123
    assert wrapper.message == "Value 123 is deprecated"
    assert wrapper.new_name is None
    assert wrapper.since is None

    structured = deprecated_member(123, new_name="NEW", since="v1.2.3")
    assert isinstance(structured, DeprecatedMember)
    assert structured.value == 123
    assert structured.message is None
    assert structured.new_name == "NEW"
    assert structured.since == "v1.2.3"


class _RenamedEnum(Enum):
    """A test enum with members deprecated in the structured form."""

    OPEN = 1
    FINISHED = 2
    PENDING = deprecated_member(1, new_name="OPEN", since="v1.2.3")
    DONE = deprecated_member(3, new_name="FINISHED")
    CLOSED = deprecated_member(
        4, "Closed tasks are gone, use FINISHED", new_name="FINISHED", since="v1.0.0"
    )


_RENAMED = f"{__name__}._RenamedEnum"


def test_deprecated_member_generates_the_warning() -> None:
    """Test that a member with only `new_name` warns with fully qualified names.

    `since` is only for the documentation, so it doesn't show up in the warning.
    """
    pending = f"{_RENAMED}.PENDING is deprecated. Use {_RENAMED}.OPEN instead."
    done = f"{_RENAMED}.DONE is deprecated. Use {_RENAMED}.FINISHED instead."

    with pytest.deprecated_call() as recorder:
        _ = _RenamedEnum.PENDING
    _assert_deprecated_member(recorder, pending)

    with pytest.deprecated_call() as recorder:
        _ = _RenamedEnum["DONE"]
    _assert_deprecated_member(recorder, done)

    with pytest.deprecated_call() as recorder:
        _ = _RenamedEnum(3)
    _assert_deprecated_member(recorder, done)

    assert _RenamedEnum.__deprecated_names__ == {
        "PENDING": pending,
        "DONE": done,
        "CLOSED": "Closed tasks are gone, use FINISHED",
    }


def test_deprecated_member_message_wins() -> None:
    """Test that a `message` replaces the generated warning, even with `new_name`."""
    with pytest.deprecated_call() as recorder:
        _ = _RenamedEnum.CLOSED
    _assert_deprecated_member(recorder, "Closed tasks are gone, use FINISHED")


def test_deprecated_member_generates_the_warning_for_nested_enums() -> None:
    """Test that the generated warning uses the qualified name of the enum."""

    class _Nested(Enum):
        """An enum defined inside a function."""

        NEW = 1
        OLD = deprecated_member(1, new_name="NEW")

    qualified = f"{__name__}.{_Nested.__qualname__}"
    assert ".<locals>._Nested" in qualified
    with pytest.deprecated_call() as recorder:
        _ = _Nested.OLD
    _assert_deprecated_member(
        recorder, f"{qualified}.OLD is deprecated. Use {qualified}.NEW instead."
    )


def test_deprecated_member_needs_a_message_or_new_name() -> None:
    """Test that a member saying neither what to warn nor what to use is refused.

    The `type: ignore` comments are part of the test: mypy reports them as unused,
    and fails, if the overloads ever accept these calls.
    """
    with pytest.raises(TypeError, match="needs message, new_name or both"):
        deprecated_member(1)  # type: ignore[call-overload]
    with pytest.raises(TypeError, match="needs message, new_name or both"):
        deprecated_member(1, None, since="v1.2.3")  # type: ignore[call-overload]
    with pytest.raises(TypeError, match="needs message, new_name or both"):
        DeprecatedMember(1)  # type: ignore[call-overload]


def test_deprecated_member_signature() -> None:
    """Test that `new_name` and `since` are keyword-only."""
    with pytest.raises(TypeError):
        deprecated_member(1, None, "NEW")  # type: ignore[call-overload]


@pytest.mark.parametrize(
    "new_name, since, error",
    [
        (0, None, TypeError),
        ("", None, ValueError),
        ("Task.NEW", None, ValueError),
        ("NEW", 0, TypeError),
        ("NEW", "", ValueError),
        ("NEW", "  ", ValueError),
    ],
    ids=[
        "new-name-type",
        "new-name-empty",
        "new-name-dotted",
        "since-type",
        "since-empty",
        "since-blank",
    ],
)
def test_deprecated_member_rejects_bad_arguments(
    new_name: Any, since: Any, error: type[Exception]
) -> None:
    """Test that `new_name` and `since` are checked when the member is declared."""
    with pytest.raises(error):
        deprecated_member(1, new_name=new_name, since=since)


def test_deprecated_member_new_name_must_be_a_member() -> None:
    """Test that a `new_name` that is not a member of the enum is refused."""
    with pytest.raises(ValueError, match="is not a member of .*_Bad: 'MISSING'"):

        class _Bad(Enum):
            """An enum pointing at a member it doesn't have."""

            NEW = 1
            OLD = deprecated_member(1, new_name="MISSING")


def test_deprecated_member_new_name_must_not_be_deprecated() -> None:
    """Test that a `new_name` pointing at a deprecated member, itself included, is refused."""
    with pytest.raises(ValueError, match="is 'OLDER', which is deprecated too"):

        class _Chained(Enum):
            """An enum pointing at another deprecated member."""

            NEW = 1
            OLDER = deprecated_member(1, new_name="NEW")
            OLD = deprecated_member(1, new_name="OLDER")

    with pytest.raises(ValueError, match="is 'OLD', which is deprecated too"):

        class _Itself(Enum):
            """An enum with a member pointing at itself."""

            NEW = 1
            OLD = deprecated_member(1, new_name="OLD")


def test_deprecated_member_helper_enum_usage() -> None:
    """Test that enums using the helper behave like those using DeprecatedMember directly."""

    class _HelperEnum(Enum):
        """Enum that uses deprecated_member for deprecated aliases."""

        ACTIVE = 1
        LEGACY_ACTIVE = deprecated_member(1, "Use ACTIVE instead")
        LEGACY_ONLY = deprecated_member(2, "Use something else")

    with pytest.deprecated_call() as recorder:
        _ = _HelperEnum.LEGACY_ACTIVE
    _assert_deprecated_member(recorder, "Use ACTIVE instead")

    with pytest.deprecated_call() as recorder:
        _ = _HelperEnum["LEGACY_ACTIVE"]
    _assert_deprecated_member(recorder, "Use ACTIVE instead")

    assert _HelperEnum(1) is _HelperEnum.ACTIVE

    with pytest.deprecated_call() as recorder:
        member = _HelperEnum(2)
    _assert_deprecated_member(recorder, "Use something else")

    with pytest.deprecated_call():
        assert member is _HelperEnum.LEGACY_ONLY


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
        PENDING = deprecated_member(1, "Use ACTIVE instead")

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

        OLD_A = deprecated_member(1, "Use something else")
        OLD_B = deprecated_member(1, "Also use something else")

    with pytest.deprecated_call():
        assert _AllDeprecated.OLD_A is _AllDeprecated.OLD_B  # type: ignore[comparison-overlap]
