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


def test_args_logged_as_original_objects(log_output):
    """
    retry args and kwargs are logged as their original Python objects, not
    repr() strings.  Processors like censoring or JSON serialization need the
    real objects, not opaque strings like "'secret'".

    Regression test for https://github.com/hynek/stamina/issues/151.
    """

    class _Sentinel:
        """Unique object to verify identity, not just equality."""

    sentinel = _Sentinel()

    @stamina.retry(on=ValueError, wait_max=0, attempts=2)
    def f(pos_arg, kw_arg=None):
        raise ValueError

    with pytest.raises(ValueError):
        f(sentinel, kw_arg=sentinel)

    assert len(log_output) == 1
    entry = log_output[0]
    # args should be the original objects, NOT repr strings like "'<...>'"
    assert entry["args"] == (sentinel,), (
        f"Expected original object in args, got {entry['args']!r}"
    )
    assert entry["kwargs"] == {"kw_arg": sentinel}, (
        f"Expected original object in kwargs, got {entry['kwargs']!r}"
    )
    # Confirm they are the exact same objects (not copies)
    assert entry["args"][0] is sentinel
    assert entry["kwargs"]["kw_arg"] is sentinel
