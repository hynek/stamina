# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import datetime as dt

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import tenacity

import stamina

from stamina._core import Attempt, _make_stop


@pytest.mark.parametrize("attempts", [None, -1, 0, 1])
@pytest.mark.parametrize("timeout", [None, -1, 0, 1, dt.timedelta(days=1)])
@pytest.mark.parametrize("duration", [1, dt.timedelta(days=1)])
def test_ok(attempts, timeout, duration):
    """
    No error, no problem.
    """

    @stamina.retry(
        on=Exception,
        attempts=attempts,
        timeout=timeout,
        wait_initial=duration,
        wait_max=duration,
        wait_jitter=duration,
    )
    def f():
        return 42

    assert 42 == f()


@pytest.mark.parametrize(
    "timeout",
    [None, 1, dt.timedelta(days=1)],
)
@pytest.mark.parametrize("duration", [0, dt.timedelta(days=0)])
def test_retries(duration, timeout, on):
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
    def f():
        nonlocal i
        if i < 1:
            i += 1
            raise ValueError

        return 42

    assert 42 == f()
    assert 1 == i


def test_wrong_exception(on):
    """
    Exceptions that are not passed as `on` are left through.
    """

    @stamina.retry(on=on)
    def f():
        raise TypeError("passed")

    with pytest.raises(TypeError, match="passed"):
        f()


def test_retry_inactive():
    """
    If inactive, don't retry.
    """
    num_called = 0

    @stamina.retry(on=Exception)
    def f():
        nonlocal num_called
        num_called += 1
        raise Exception("passed")

    stamina.set_active(False)

    with pytest.raises(Exception, match="passed"):
        f()

    assert 1 == num_called


def test_retry_inactive_block():
    """
    If inactive, don't retry.
    """
    num_called = 0

    stamina.set_active(False)

    with pytest.raises(Exception, match="passed"):  # noqa: PT012
        for attempt in stamina.retry_context(on=ValueError):
            with attempt:
                num_called += 1
                raise Exception("passed")

    assert 1 == num_called


def test_retry_inactive_ok():
    """
    If inactive, the happy path still works.
    """
    num_called = 0

    @stamina.retry(on=Exception)
    def f():
        nonlocal num_called
        num_called += 1

    stamina.set_active(False)

    f()

    assert 1 == num_called


def test_retry_inactive_block_ok():
    """
    If inactive, the happy path still works.
    """
    num_called = 0

    stamina.set_active(False)

    for attempt in stamina.retry_context(on=ValueError):
        with attempt:
            num_called += 1

    assert 1 == num_called


def test_retry_block(on):
    """
    Sync retry_context blocks are retried.
    """
    i = 0

    for attempt in stamina.retry_context(on=on, wait_max=0):
        with attempt:
            i += 1

            assert i == attempt.num
            assert 0.0 == attempt.next_wait
            assert f"<Attempt num={i}, next_wait=0.0>" == repr(attempt)

            if i < 2:
                raise ValueError

    assert 2 == i


def test_next_wait():
    """
    The next_wait property is updated.
    """

    for attempt in stamina.retry_context(on=ValueError, wait_max=0.0001):
        with attempt:
            assert pytest.approx(0.0001) == attempt.next_wait

            if attempt.num == 1:
                raise ValueError


def test_backoff_computation_clamps():
    """
    The backoff returned by _RetryContextIterator._backoff_for_attempt_number
    and _RetryContextIterator._jittered_backoff_for_rcs never exceeds wait_max.
    """
    rci = stamina.retry_context(on=ValueError, wait_max=0.42)

    for i in range(1, 10):
        backoff = rci._backoff_for_attempt_number(i)
        assert backoff <= 0.42

        jittered = rci._jittered_backoff_for_rcs(
            SimpleNamespace(attempt_number=i)
        )
        assert jittered <= 0.42


def test_testing_mode():
    """
    Testing mode can be set and reset.
    """
    stamina.set_testing(True, attempts=3)

    assert stamina.is_testing()

    with pytest.raises(ValueError):  # noqa: PT012
        for attempt in stamina.retry_context(on=ValueError):
            assert 0.0 == attempt.next_wait

            with attempt:
                raise ValueError

    assert 3 == attempt.num

    stamina.set_testing(False)

    assert not stamina.is_testing()

    for attempt in stamina.retry_context(on=ValueError):
        assert 0.0 != attempt.next_wait
        break


class TestMakeStop:
    def test_never(self):
        """
        If all conditions are None, return stop_never.
        """
        assert tenacity.stop_never is _make_stop(attempts=None, timeout=None)


class TestRetryingCaller:
    def test_ok(self):
        """
        No error, no problem.
        """
        rc = stamina.RetryingCaller().on(BaseException)

        def f():
            return 42

        assert 42 == rc(f)

    def test_retries(self, on):
        """
        Retries if the specific error is raised. Arguments are passed through.
        """
        i = 0

        def f(*args, **kw):
            nonlocal i
            if i < 1:
                i += 1
                raise ValueError

            return args, kw

        bound_rc = stamina.RetryingCaller(wait_max=0).on(on)

        args, kw = bound_rc(f, 42, foo="bar")

        assert 1 == i
        assert (42,) == args
        assert {"foo": "bar"} == kw

    def test_repr(self):
        """
        repr() is useful.
        """
        rc = stamina.RetryingCaller(
            attempts=42,
            timeout=13.0,
            wait_initial=23,
            wait_max=123,
            wait_jitter=0.42,
            wait_exp_base=666,
        )

        r = repr(rc)

        assert (
            "<RetryingCaller(attempts=42, timeout=13.0, "
            "wait_exp_base=666, wait_initial=23, wait_jitter=0.42, "
            "wait_max=123)>"
        ) == r
        assert f"<BoundRetryingCaller(ValueError, {r})>" == repr(
            rc.on(ValueError)
        )


def test_testing_mode_context():
    """
    Testing mode context manager works with sync code.
    """
    assert not stamina.is_testing()

    with stamina.set_testing(True, attempts=3):
        assert stamina.is_testing()

        with pytest.raises(ValueError):  # noqa: PT012
            for attempt in stamina.retry_context(on=ValueError):
                assert 0.0 == attempt.next_wait

                with attempt:
                    raise ValueError

        assert 3 == attempt.num

    assert not stamina.is_testing()


class TestGeneratorFunctionDecoration:
    @pytest.mark.parametrize("attempts", [None, 1])
    @pytest.mark.parametrize("timeout", [None, 1, dt.timedelta(days=1)])
    @pytest.mark.parametrize("duration", [1, dt.timedelta(days=1)])
    def test_ok(self, attempts, timeout, duration):
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
            def f(self):
                yield 42

        @stamina.retry(
            on=Exception,
            attempts=attempts,
            timeout=timeout,
            wait_initial=duration,
            wait_max=duration,
            wait_jitter=duration,
        )
        def f():
            yield 42

        assert 42 == next(f())
        assert 42 == next(C().f())

    @pytest.mark.parametrize(
        "timeout",
        [None, 1, dt.timedelta(days=1)],
    )
    @pytest.mark.parametrize("duration", [0, dt.timedelta(days=0)])
    def test_retries(self, duration, timeout, on):
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
        def f():
            nonlocal i
            if i < 1:
                i += 1
                raise ValueError

            yield 42

        assert 42 == next(f())
        assert 1 == i

    @pytest.mark.parametrize(
        "timeout",
        [None, 1, dt.timedelta(days=1)],
    )
    @pytest.mark.parametrize("duration", [0, dt.timedelta(days=0)])
    def test_retries_also_after_yields(self, duration, timeout, on):
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
        def f():
            yield 42

            nonlocal i
            if i < 1:
                i += 1
                raise ValueError

        assert [42, 42] == list(f())
        assert 1 == i

    def test_forwards_send(self):
        """
        Values sent via send() reach the wrapped generator unchanged.
        """
        sent_values = []

        @stamina.retry(on=Exception)
        def gen():
            sent = yield "ready"
            sent_values.append(sent)
            yield sent

        g = gen()

        assert "ready" == next(g)
        assert "sentinel" == g.send("sentinel")
        assert ["sentinel"] == sent_values

    def test_forwards_throw(self):
        """
        Exceptions raised via throw() reach the wrapped generator unchanged.
        """
        received = []

        @stamina.retry(on=Exception, wait_max=0)
        def gen():
            try:
                yield "ready"
            except RuntimeError as err:
                received.append(err)
                raise

        g = gen()

        assert "ready" == next(g)

        exc = RuntimeError("boom")

        restart_value = g.throw(exc)

        assert "ready" == restart_value
        assert received == [exc]

    def test_wrong_exception(self, on):
        """
        Exceptions that are not passed as `on` are left through.
        """

        @stamina.retry(on=on)
        def f():
            yield
            raise TypeError("passed")

        with pytest.raises(TypeError, match="passed"):
            for _ in f():
                pass

    def test_inactive(self):
        """
        If inactive, don't retry.
        """
        num_called = 0

        @stamina.retry(on=Exception)
        def f():
            nonlocal num_called
            num_called += 1
            yield
            raise Exception("passed")

        stamina.set_active(False)

        with pytest.raises(Exception, match="passed"):
            for _ in f():
                pass

        assert 1 == num_called

    def test_retry_inactive_ok(self):
        """
        If inactive, the happy path still works.
        """
        num_called = 0

        @stamina.retry(on=Exception)
        def f():
            nonlocal num_called
            num_called += 1
            yield

        stamina.set_active(False)

        next(f())

        assert 1 == num_called

    def test_wrapper_passes_through_return_value(self):
        """
        If no error, return should be passed through.
        """

        @stamina.retry(on=Exception)
        def f():
            yield 1
            yield 2
            return "Polizei"

        gen = f()
        assert 1 == next(gen)
        assert 2 == next(gen)

        with pytest.raises(StopIteration) as exc_info:
            next(gen)

        assert "Polizei" == exc_info.value.value


def test_attempt_next_wait():
    """
    next_wait reflects the attempt number. The next wait is computed based on
    the current attempt number.
    """
    am = Mock(retry_state=Mock())

    def next_wait_fn(attempt_num: int) -> float:
        return attempt_num

    for i in range(1, 3):
        am.retry_state.attempt_number = i
        attempt = Attempt(am, next_wait_fn)

        assert i == attempt.next_wait
