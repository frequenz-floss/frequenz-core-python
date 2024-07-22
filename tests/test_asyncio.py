# License: MIT
# Copyright © 2022 Frequenz Energy-as-a-Service GmbH

"""Tests for the asyncio module."""

import asyncio
from typing import Literal, assert_never

import async_solipsism
import pytest

from frequenz.core.asyncio import BackgroundService


# This method replaces the event loop for all tests in the file.
@pytest.fixture
def event_loop_policy() -> async_solipsism.EventLoopPolicy:
    """Return an event loop policy that uses the async solipsism event loop."""
    return async_solipsism.EventLoopPolicy()


class FakeService(BackgroundService):
    """A background service that does nothing."""

    def __init__(
        self,
        *,
        unique_id: str | None = None,
        sleep: float | None = None,
        exc: BaseException | None = None,
    ) -> None:
        """Initialize a new FakeService."""
        super().__init__(unique_id=unique_id)
        self._sleep = sleep
        self._exc = exc

    def start(self) -> None:
        """Start this service."""

        async def nop() -> None:
            if self._sleep is not None:
                await asyncio.sleep(self._sleep)
            if self._exc is not None:
                raise self._exc

        self._tasks.add(asyncio.create_task(nop(), name="nop"))


async def test_construction_defaults() -> None:
    """Test the construction of a background service with default arguments."""
    fake_service = FakeService()
    assert fake_service.unique_id == hex(id(fake_service))[2:]
    assert fake_service.tasks == set()
    assert fake_service.is_running is False
    assert str(fake_service) == f"FakeService[{fake_service.unique_id}]"
    assert (
        repr(fake_service)
        == f"FakeService(unique_id={fake_service.unique_id!r}, tasks=set())"
    )


async def test_construction_custom() -> None:
    """Test the construction of a background service with a custom unique ID."""
    fake_service = FakeService(unique_id="test")
    assert fake_service.unique_id == "test"
    assert fake_service.tasks == set()
    assert fake_service.is_running is False


async def test_start_await() -> None:
    """Test a background service starts and can be awaited."""
    fake_service = FakeService(unique_id="test")
    assert fake_service.unique_id == "test"
    assert fake_service.is_running is False

    # Is a no-op if the service is not running
    await fake_service.stop()
    assert fake_service.is_running is False

    fake_service.start()
    assert fake_service.is_running is True

    # Should stop immediately
    async with asyncio.timeout(1.0):
        await fake_service

    assert fake_service.is_running is False


async def test_start_stop() -> None:
    """Test a background service starts and stops correctly."""
    fake_service = FakeService(unique_id="test", sleep=2.0)
    assert fake_service.unique_id == "test"
    assert fake_service.is_running is False

    # Is a no-op if the service is not running
    await fake_service.stop()
    assert fake_service.is_running is False

    fake_service.start()
    assert fake_service.is_running is True

    await asyncio.sleep(1.0)
    assert fake_service.is_running is True

    await fake_service.stop()
    assert fake_service.is_running is False

    await fake_service.stop()
    assert fake_service.is_running is False


@pytest.mark.parametrize("method", ["await", "wait", "stop"])
async def test_start_and_crash(
    method: Literal["await"] | Literal["wait"] | Literal["stop"],
) -> None:
    """Test a background service reports when crashing."""
    exc = RuntimeError("error")
    fake_service = FakeService(unique_id="test", exc=exc)
    assert fake_service.unique_id == "test"
    assert fake_service.is_running is False

    fake_service.start()
    with pytest.raises(BaseExceptionGroup) as exc_info:
        match method:
            case "await":
                await fake_service
            case "wait":
                await fake_service.wait()
            case "stop":
                # Give the service some time to run and crash, otherwise stop() will
                # cancel it before it has a chance to crash
                await asyncio.sleep(1.0)
                await fake_service.stop()
            case _:
                assert_never(method)

    rt_errors, rest_errors = exc_info.value.split(RuntimeError)
    assert rt_errors is not None
    assert rest_errors is None
    assert len(rt_errors.exceptions) == 1
    assert rt_errors.exceptions[0] is exc


async def test_async_context_manager() -> None:
    """Test a background service works as an async context manager."""
    async with FakeService(unique_id="test", sleep=1.0) as fake_service:
        assert fake_service.is_running is True
        # Is a no-op if the service is running
        fake_service.start()
        await asyncio.sleep(0)
        assert fake_service.is_running is True

    assert fake_service.is_running is False
