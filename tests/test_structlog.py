# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import pytest

import stamina


structlog = pytest.importorskip("structlog")


@pytest.fixture(name="log_output")
def _log_output():
    from structlog.testing import LogCapture

    log_output = LogCapture()
    structlog.configure(processors=[log_output])

    return log_output.entries


def test_decorator_sync(log_output):
    """
    Retries decorators log correct name / arguments.
    """

    @stamina.retry(on=ValueError, wait_max=0, attempts=2)
    def f():
        raise ValueError

    with pytest.raises(ValueError):
        f()

    assert [
        {
            "args": (),
            "attempt": 1,
            "slept": 0.0,
            "callable": "tests.test_structlog.test_decorator_sync.<locals>.f",
            "error": "ValueError()",
            "event": "stamina.retry_scheduled",
            "kwargs": {},
            "log_level": "warning",
        },
    ] == log_output


async def test_decorator_async(log_output):
    """
    Retries decorators log correct name / arguments.
    """

    @stamina.retry(on=ValueError, wait_max=0, attempts=2)
    async def f():
        raise ValueError

    with pytest.raises(ValueError):
        await f()

    assert [
        {
            "args": (),
            "attempt": 1,
            "slept": 0.0,
            "callable": "tests.test_structlog.test_decorator_async.<locals>.f",
            "error": "ValueError()",
            "event": "stamina.retry_scheduled",
            "kwargs": {},
            "log_level": "warning",
        },
    ] == log_output


def test_context_sync(log_output):
    """
    Retries context blocks log correct name / arguments.
    """
    from tests.test_sync import test_retry_block

    test_retry_block()

    assert [
        {
            "callable": "<context block>",
            "attempt": 1,
            "slept": 0.0,
            "error": "ValueError()",
            "args": (),
            "kwargs": {},
            "event": "stamina.retry_scheduled",
            "log_level": "warning",
        }
    ] == log_output


async def test_context_async(log_output):
    """
    Retries context blocks log correct name / arguments.
    """
    from tests.test_async import test_retry_block

    await test_retry_block()

    assert [
        {
            "callable": "<context block>",
            "attempt": 1,
            "slept": 0.0,
            "error": "ValueError()",
            "args": (),
            "kwargs": {},
            "event": "stamina.retry_scheduled",
            "log_level": "warning",
        }
    ] == log_output
