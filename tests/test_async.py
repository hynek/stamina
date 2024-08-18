# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import datetime as dt

import pytest

import stamina


pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("attempts", [None, 1])
@pytest.mark.parametrize("timeout", [None, 1, dt.timedelta(days=1)])
@pytest.mark.parametrize("duration", [1, dt.timedelta(days=1)])
async def test_ok(attempts, timeout, duration):
    """
    No error, no problem.
    """

    class C:
        @stamina.retry(
            on=Exception,
            attempts=attempts,
            timeout=timeout,
            wait_initial=duration,
            wait_max=duration,
            wait_jitter=duration,
        )
        async def f(self):
            return 42

    @stamina.retry(
        on=Exception,
        attempts=attempts,
        timeout=timeout,
        wait_initial=duration,
        wait_max=duration,
        wait_jitter=duration,
    )
    async def f():
        return 42

    assert 42 == await f()
    assert 42 == await C().f()


@pytest.mark.parametrize("timeout", [None, 1, dt.timedelta(days=1)])
@pytest.mark.parametrize("duration", [0, dt.timedelta(days=0)])
async def test_retries(duration, timeout, on):
    """
    Retries if the specific error is raised.
    """
    i = 0

    @stamina.retry(
        on=on,
        timeout=timeout,
        wait_max=duration,
        wait_initial=duration,
        wait_jitter=duration,
    )
    async def f():
        nonlocal i
        if i == 0:
            i += 1
            raise ValueError

        return 42

    assert 42 == await f()
    assert 1 == i


async def test_retries_method(on):
    """
    Retries if the specific error is raised.
    """
    i = 0

    class C:
        @stamina.retry(on=on, wait_max=0)
        async def f(self):
            nonlocal i
            if i == 0:
                i += 1
                raise ValueError

            return 42

    assert 42 == await C().f()
    assert 1 == i


async def test_wrong_exception(on):
    """
    Exceptions that are not passed as `on` are left through.
    """

    @stamina.retry(on=on)
    async def f():
        raise TypeError("passed")

    with pytest.raises(TypeError, match="passed"):
        await f()


async def test_retry_inactive():
    """
    If inactive, don't retry.
    """
    num_called = 0

    @stamina.retry(on=Exception)
    async def f():
        nonlocal num_called
        num_called += 1
        raise Exception("passed")

    stamina.set_active(False)

    with pytest.raises(Exception, match="passed"):
        await f()

    assert 1 == num_called


async def test_retry_inactive_block():
    """
    If inactive, don't retry.
    """
    num_called = 0

    stamina.set_active(False)

    with pytest.raises(Exception, match="passed"):  # noqa: PT012
        async for attempt in stamina.retry_context(on=ValueError):
            with attempt:
                num_called += 1
                raise Exception("passed")

    assert 1 == num_called


async def test_retry_inactive_ok():
    """
    If inactive, the happy path still works.
    """
    num_called = 0

    @stamina.retry(on=Exception)
    async def f():
        nonlocal num_called
        num_called += 1

    stamina.set_active(False)

    await f()

    assert 1 == num_called


async def test_retry_inactive_block_ok():
    """
    If inactive, the happy path still works.
    """
    num_called = 0

    stamina.set_active(False)

    async for attempt in stamina.retry_context(on=ValueError):
        with attempt:
            num_called += 1

    assert 1 == num_called


async def test_retry_block(on):
    """
    Async retry_context blocks are retried.
    """
    num_called = 0

    async for attempt in stamina.retry_context(on=on, wait_max=0):
        with attempt:
            num_called += 1

            assert num_called == attempt.num

            if num_called < 2:
                raise ValueError

    assert 2 == num_called


async def test_next_wait():
    """
    The next_wait property is updated.
    """
    i = 0

    async for attempt in stamina.retry_context(on=ValueError, wait_max=0.001):
        with attempt:
            if i == 0:
                assert 0.0 == attempt.next_wait

                i += 1
                raise ValueError

            assert pytest.approx(0.001) == attempt.next_wait


async def test_retry_blocks_can_be_disabled():
    """
    Async context retries respect the config.
    """
    stamina.set_active(False)
    num_called = 0

    with pytest.raises(Exception, match="passed"):  # noqa: PT012
        async for attempt in stamina.retry_context(on=Exception, attempts=2):
            with attempt:
                num_called += 1
                raise Exception("passed")

    assert 1 == num_called


class TestAsyncRetryingCaller:
    async def test_ok(self):
        """
        No error, no problem.
        """
        arc = stamina.AsyncRetryingCaller().on(BaseException)

        async def f():
            return 42

        assert 42 == await arc(f)

    async def test_retries(self, on):
        """
        Retries if the specific error is raised. Arguments are passed through.
        """
        i = 0

        async def f(*args, **kw):
            nonlocal i
            if i < 1:
                i += 1
                raise ValueError

            return args, kw

        arc = stamina.AsyncRetryingCaller().on(on)

        args, kw = await arc(f, 42, foo="bar")

        assert 1 == i
        assert (42,) == args
        assert {"foo": "bar"} == kw

    def test_repr(self):
        """
        repr() is useful
        """
        arc = stamina.AsyncRetryingCaller(
            attempts=42,
            timeout=13.0,
            wait_initial=23,
            wait_max=123,
            wait_jitter=0.42,
            wait_exp_base=666,
        )

        r = repr(arc)

        assert (
            "<AsyncRetryingCaller(attempts=42, timeout=13.0, "
            "wait_exp_base=666, wait_initial=23, wait_jitter=0.42, "
            "wait_max=123)>"
        ) == r
        assert f"<BoundAsyncRetryingCaller(ValueError, {r})>" == repr(
            arc.on(ValueError)
        )
