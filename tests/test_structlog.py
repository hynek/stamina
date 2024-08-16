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
            "retry_num": 1,
            "wait_for": 0.0,
            "waited_so_far": 0.0,
            "callable": "tests.test_structlog.test_decorator_sync.<locals>.f",
            "caused_by": "ValueError()",
            "event": "stamina.retry_scheduled",
            "kwargs": {},
            "log_level": "warning",
        },
    ] == log_output


@pytest.mark.anyio
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
            "retry_num": 1,
            "wait_for": 0.0,
            "waited_so_far": 0.0,
            "callable": "tests.test_structlog.test_decorator_async.<locals>.f",
            "caused_by": "ValueError()",
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

    test_retry_block(ValueError)

    assert [
        {
            "callable": "<context block>",
            "retry_num": 1,
            "wait_for": 0.0,
            "waited_so_far": 0.0,
            "caused_by": "ValueError()",
            "args": (),
            "kwargs": {},
            "event": "stamina.retry_scheduled",
            "log_level": "warning",
        }
    ] == log_output


@pytest.mark.anyio
async def test_context_async(log_output):
    """
    Retries context blocks log correct name / arguments.
    """
    from tests.test_async import test_retry_block

    await test_retry_block(ValueError)

    assert [
        {
            "callable": "<context block>",
            "retry_num": 1,
            "wait_for": 0.0,
            "waited_so_far": 0.0,
            "caused_by": "ValueError()",
            "args": (),
            "kwargs": {},
            "event": "stamina.retry_scheduled",
            "log_level": "warning",
        }
    ] == log_output
