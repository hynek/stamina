# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import datetime as dt
import time

import pytest

import stamina


pytestmark = pytest.mark.anyio


@pytest.mark.parametrize("attempts", [None, -1, 0, 1])
@pytest.mark.parametrize("timeout", [None, -1, 0, 1, dt.timedelta(days=1)])
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
    async for attempt in stamina.retry_context(on=ValueError, wait_max=0.0001):
        with attempt:
            assert pytest.approx(0.0001) == attempt.next_wait

            if attempt.num == 1:
                raise ValueError


async def test_testing_mode():
    """
    Testing mode can be set and reset.
    """
    stamina.set_testing(True, attempts=3)

    assert stamina.is_testing()

    with pytest.raises(ValueError):  # noqa: PT012
        async for attempt in stamina.retry_context(on=ValueError):
            assert 0.0 == attempt.next_wait

            with attempt:
                raise ValueError

    assert 3 == attempt.num

    stamina.set_testing(False)

    assert not stamina.is_testing()

    async for attempt in stamina.retry_context(on=ValueError):
        assert 0.0 != attempt.next_wait
        break


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

        arc = stamina.AsyncRetryingCaller(wait_max=0).on(on)

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


async def test_testing_mode_context():
    """
    Testing mode context manager works with async code.
    """
    assert not stamina.is_testing()

    with stamina.set_testing(True, attempts=3):
        assert stamina.is_testing()

        with pytest.raises(ValueError):  # noqa: PT012
            async for attempt in stamina.retry_context(on=ValueError):
                assert 0.0 == attempt.next_wait

                with attempt:
                    raise ValueError

        assert 3 == attempt.num

    assert not stamina.is_testing()


class TestAsyncGeneratorFunctionDecoration:
    @pytest.mark.parametrize("attempts", [None, 1])
    @pytest.mark.parametrize("timeout", [None, 1, dt.timedelta(days=1)])
    @pytest.mark.parametrize("duration", [1, dt.timedelta(days=1)])
    async def test_ok(self, attempts, timeout, duration):
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
                yield 42

        @stamina.retry(
            on=Exception,
            attempts=attempts,
            timeout=timeout,
            wait_initial=duration,
            wait_max=duration,
            wait_jitter=duration,
        )
        async def f():
            yield 42

        assert [42] == [item async for item in f()]
        assert [42] == [item async for item in C().f()]

    @pytest.mark.parametrize("timeout", [None, 1, dt.timedelta(days=1)])
    @pytest.mark.parametrize("duration", [0, dt.timedelta(days=0)])
    async def test_retries(self, duration, timeout, on):
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

            yield 42

        assert [42] == [item async for item in f()]
        assert 1 == i

    async def test_forwards_asend(self):
        """
        Values sent via asend() reach the wrapped generator unchanged.
        """
        sent_values = []

        @stamina.retry(on=Exception)
        async def gen():
            sent = yield "ready"
            sent_values.append(sent)
            yield sent

        agen = gen()

        assert "ready" == await anext(agen)
        assert "sentinel" == await agen.asend("sentinel")
        assert ["sentinel"] == sent_values

        await agen.aclose()

    async def test_forwards_athrow(self):
        """
        Exceptions raised via athrow() reach the wrapped generator unchanged.
        """
        received = []

        @stamina.retry(on=Exception, wait_max=0)
        async def gen():
            try:
                yield "ready"
            except RuntimeError as err:
                received.append(err)
                raise

        agen = gen()

        assert "ready" == await anext(agen)

        exc = RuntimeError("boom")

        restart_value = await agen.athrow(exc)

        assert "ready" == restart_value
        assert received == [exc]

        await agen.aclose()

    async def test_stops_when_wrapped_generator_is_empty(self):
        """
        Wrapping an empty async generator yields no items and exits cleanly.
        """

        @stamina.retry(on=Exception)
        async def gen():
            if False:
                yield None

        assert [] == [item async for item in gen()]

    async def test_athrow_that_gets_suppressed(self):
        """
        If the wrapped generator swallows an exception and exits, athrow()
        stops.
        """

        @stamina.retry(on=Exception)
        async def gen():
            try:
                yield "ready"
            except RuntimeError:
                return

        agen = gen()

        assert "ready" == await anext(agen)

        with pytest.raises(StopAsyncIteration):
            await agen.athrow(RuntimeError("boom"))

        await agen.aclose()

    @pytest.mark.parametrize(
        "timeout",
        [None, 1, dt.timedelta(days=1)],
    )
    @pytest.mark.parametrize("duration", [0, dt.timedelta(days=0)])
    async def test_retries_also_after_yields(self, duration, timeout, on):
        """
        Retries if the specific error is raised after yielding.
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
            yield 42

            nonlocal i
            if i < 1:
                i += 1
                raise ValueError

        assert [42, 42] == [item async for item in f()]
        assert 1 == i

    async def test_retries_method(self, on):
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

                yield 42

        items = [item async for item in C().f()]
        assert [42] == items
        assert 1 == i

    async def test_wrong_exception(self, on):
        """
        Exceptions that are not passed as `on` are left through.
        """

        @stamina.retry(on=on)
        async def f():
            yield
            raise TypeError("passed")

        with pytest.raises(TypeError, match="passed"):
            async for _ in f():
                pass

    async def test_retry_inactive(self):
        """
        If inactive, don't retry.
        """
        num_called = 0

        @stamina.retry(on=Exception)
        async def f():
            nonlocal num_called
            num_called += 1
            yield
            raise Exception("passed")

        stamina.set_active(False)

        with pytest.raises(Exception, match="passed"):
            async for _ in f():
                pass

        assert 1 == num_called

    async def test_retry_inactive_ok(self):
        """
        If inactive, the happy path still works.
        """
        num_called = 0

        @stamina.retry(on=Exception)
        async def f():
            nonlocal num_called
            num_called += 1
            yield

        stamina.set_active(False)

        items = [item async for item in f()]
        assert [None] == items

        assert 1 == num_called


class TestBackoffHookAsync:
    @pytest.mark.anyio
    @pytest.mark.usefixtures("anyio_backend")
    async def test_backoff_hook_returns_float_async(self):
        """
        If a backoff hook returns a float, it is used as the backoff duration.
        """
        attempts = 0

        @stamina.retry(on=lambda exc: 0.0, wait_initial=5, attempts=3)
        async def f():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("retry")
            return 42

        started_at = time.perf_counter()
        result = await f()
        duration = time.perf_counter() - started_at

        assert 42 == result
        assert 3 == attempts
        assert duration < 5

    @pytest.mark.anyio
    @pytest.mark.usefixtures("anyio_backend")
    async def test_backoff_hook_with_async_retry_context(self):
        """
        Backoff hooks work with async retry_context.
        """
        attempts = 0

        started_at = time.perf_counter()
        async for attempt in stamina.retry_context(
            on=lambda exc: 0.0, wait_initial=5, attempts=3
        ):
            with attempt:
                attempts += 1
                if attempts < 2:
                    raise ValueError("retry")

        duration = time.perf_counter() - started_at

        assert 2 == attempts
        assert duration < 5
