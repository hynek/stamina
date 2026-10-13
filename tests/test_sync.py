# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import datetime as dt
import subprocess
import sys
import time

from textwrap import dedent
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import tenacity

from dirty_equals import IsFloat

import stamina

from stamina._core import Attempt, _make_stop
from stamina.exceptions import TryAgain


@pytest.mark.parametrize("attempts", [None, -1, 0, 1])
@pytest.mark.parametrize("timeout", [None, -1, 1, dt.timedelta(days=1)])
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
    "timeout", [0, 0.0, dt.timedelta(0)], ids=["int", "float", "timedelta"]
)
def test_timeout_zero_warns(timeout):
    """
    timeout=0 raises a helpful warning with the correct code location.
    """
    with pytest.warns(
        UserWarning,
        match="timeout=0 means no retries will be attempted",
    ) as wi:
        stamina.retry_context(on=Exception, timeout=timeout)

    assert wi.pop().filename.endswith("test_sync.py")

    with pytest.warns(
        UserWarning,
        match="timeout=0 means no retries will be attempted",
    ) as wi:

        @stamina.retry(on=ValueError, timeout=timeout)
        def func():
            pass

    assert wi.pop().filename.endswith("test_sync.py")


@pytest.mark.parametrize(
    ("kw", "make_exc"),
    [
        ({"on": ValueError, "wait_initial": 2, "wait_max": 2}, ValueError),
        ({"on": lambda _: 2.0}, ValueError),
        ({"on": ValueError}, lambda: TryAgain(after=2)),
    ],
    ids=["backoff", "backoff-hook", "try-again-after"],
)
def test_gives_up_if_backoff_exceeds_timeout(kw, make_exc):
    """
    If the next backoff would end after timeout, stamina gives up right away,
    instead of sleeping past the deadline only to give up afterwards.
    """
    raised = []

    @stamina.retry(timeout=1, wait_jitter=0, **kw)
    def f():
        raised.append(make_exc())
        raise raised[-1]

    start = time.monotonic()

    with pytest.raises(Exception) as ei:
        f()

    assert [ei.value] == raised
    assert time.monotonic() - start < 1


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


class CustomBaseError(BaseException):
    pass


@pytest.mark.parametrize(
    "on",
    [
        CustomBaseError,
        (ValueError, CustomBaseError),
        lambda exc: isinstance(exc, CustomBaseError),
    ],
)
def test_retries_base_exceptions(on):
    """
    If on matches a BaseException, it is retried.
    """
    i = 0

    @stamina.retry(on=on, wait_max=0)
    def f():
        nonlocal i
        if i < 1:
            i += 1
            raise CustomBaseError

        return 42

    assert 42 == f()
    assert 1 == i


def test_try_again(on):
    """
    Raising TryAgain forces a retry, whatever on is.
    """
    i = 0

    @stamina.retry(on=on, wait_max=0)
    def f():
        nonlocal i
        if i < 1:
            i += 1
            raise TryAgain

        return 42

    assert 42 == f()
    assert 1 == i


def test_try_again_respects_attempts():
    """
    TryAgain doesn't add attempts. If the last attempt raises it, the caller
    gets it.
    """
    num_called = 0

    @stamina.retry(on=ValueError, wait_max=0, attempts=2)
    def f():
        nonlocal num_called
        num_called += 1
        raise TryAgain

    with pytest.raises(TryAgain):
        f()

    assert 2 == num_called


def test_try_again_raises_cause():
    """
    If TryAgain was raised from another exception, the caller gets that
    exception unchanged when stamina runs out of attempts.
    """
    raised = []

    def connect():
        raise OSError

    def request():
        try:
            connect()
        except OSError as e:
            raise RuntimeError from e

    @stamina.retry(on=ValueError, wait_max=0, attempts=2)
    def f():
        try:
            request()
        except RuntimeError as e:
            raised.append(e)
            raise TryAgain from e

    with pytest.raises(RuntimeError) as ei:
        f()

    assert 2 == len(raised)
    assert raised[-1] is ei.value
    assert isinstance(ei.value.__cause__, OSError)
    assert ei.value.__cause__ is ei.value.__context__


def test_try_again_ignores_context():
    """
    An explicit cause replaces TryAgain.
    """

    @stamina.retry(on=ValueError, wait_max=0, attempts=2)
    def f():
        raise TryAgain

    try:
        {}["missing"]
    except KeyError:
        with pytest.raises(TryAgain):
            f()


def test_try_again_raises_cause_when_inactive():
    """
    With retries deactivated, the caller gets the cause after the only
    attempt.
    """
    stamina.set_active(False)

    @stamina.retry(on=ValueError)
    def f():
        raise TryAgain from KeyError("cause")

    with pytest.raises(KeyError, match="cause"):
        f()


@pytest.fixture(name="waits")
def _waits():
    """
    Record the backoff of each scheduled retry.
    """
    waits = []
    stamina.instrumentation.set_on_retry_hooks(
        [lambda details: waits.append(details.wait_for)]
    )

    return waits


def raise_try_again_once(after):
    """
    Create a function that raises TryAgain(after=after) on its first call and
    returns 42 on its second.
    """
    num_called = 0

    def f():
        nonlocal num_called
        num_called += 1
        if num_called == 1:
            raise TryAgain(after=after)

        return 42

    return f


@pytest.mark.parametrize("after", [0.001, dt.timedelta(seconds=0.001)])
def test_try_again_after(waits, after):
    """
    TryAgain(after=...) waits that long before the next attempt, even if it's
    longer than wait_max. A server's Retry-After beats our own limits.
    """
    f = stamina.retry(
        on=ValueError, wait_initial=0, wait_max=0.01, wait_jitter=0
    )(raise_try_again_once(after))

    assert 42 == f()
    assert [0.001] == waits


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (dt.timedelta(seconds=0.05), IsFloat(gt=0, le=0.05)),
        (-dt.timedelta(hours=1), 0.0),
    ],
)
def test_try_again_after_datetime(waits, offset, expected):
    """
    TryAgain(after=<datetime>) waits until then. A datetime in the past
    doesn't add any wait.
    """
    f = stamina.retry(on=ValueError, wait_initial=0, wait_jitter=0)(
        raise_try_again_once(dt.datetime.now(dt.timezone.utc) + offset)
    )

    assert 42 == f()
    assert [expected] == waits


def test_try_again_after_is_lower_bound(waits):
    """
    If the regular backoff is longer than after, stamina uses the regular
    backoff.
    """
    f = stamina.retry(on=ValueError, wait_initial=0.002, wait_jitter=0)(
        raise_try_again_once(0.001)
    )

    assert 42 == f()
    assert [0.002] == waits


def test_try_again_after_gets_jitter(waits):
    """
    stamina adds jitter to after, so clients that got the same Retry-After
    don't come back at the same time.
    """
    f = stamina.retry(on=ValueError, wait_initial=0, wait_jitter=0.001)(
        raise_try_again_once(0.001)
    )

    assert 42 == f()
    assert [IsFloat(ge=0.001, le=0.002)] == waits


def test_try_again_after_ignored_in_testing_mode(waits):
    """
    In testing mode, after is ignored like all other backoffs.
    """
    f = stamina.retry(on=ValueError)(raise_try_again_once(3600))

    with stamina.set_testing(True, attempts=2):
        assert 42 == f()

    assert [0.0] == waits


def test_try_again_after_naive_datetime():
    """
    A naive datetime is rejected right away, because stamina can't compare it
    to the current time.
    """
    with pytest.raises(TypeError, match="timezone-aware"):
        TryAgain(after=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None))


def test_tenacity_try_again_is_deprecated():
    """
    Raising Tenacity's TryAgain still forces a retry, but warns. The warning
    points at the code that raised it, so users find what they must change.
    """
    i = 0

    @stamina.retry(on=ValueError, wait_max=0)
    def f():
        nonlocal i
        if i < 1:
            i += 1
            raise tenacity.TryAgain

        return 42

    with pytest.warns(
        DeprecationWarning, match=r"Raise stamina\.exceptions\.TryAgain"
    ) as ws:
        rv = f()

    assert 42 == rv
    assert 1 == i
    assert __file__ == ws.pop(DeprecationWarning).filename


@pytest.mark.parametrize("mode", ["-c", "-"])
def test_tenacity_try_again_in_main(mode):
    """
    Tenacity's TryAgain warns and retries from python -c or stdin, even when
    __main__ has a built-in loader.
    """
    code = dedent("""\
        import stamina
        import tenacity

        for attempt in stamina.retry_context(
            on=ValueError, attempts=2, wait_max=0
        ):
            with attempt:
                if attempt.num == 1:
                    raise tenacity.TryAgain

        assert 2 == attempt.num
        """)
    result = subprocess.run(  # noqa: S603 -- All inputs are defined in this test.
        [sys.executable, "-Wdefault", mode, *([code] if mode == "-c" else [])],
        input=code,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert 0 == result.returncode, result.stderr
    assert "DeprecationWarning: Raising tenacity.TryAgain" in result.stderr


def test_wrong_exception(on):
    """
    Exceptions that are not passed as `on` are left through without retrying.
    """
    num_called = 0

    @stamina.retry(on=on)
    def f():
        nonlocal num_called
        num_called += 1
        raise TypeError("passed")

    with pytest.raises(TypeError, match="passed"):
        f()

    assert 1 == num_called


def test_wrong_exception_context(on):
    """
    Exceptions that are not passed as `on` leave a retry_context block without
    retrying.
    """
    num_called = 0

    with pytest.raises(TypeError, match="passed"):  # noqa: PT012
        for attempt in stamina.retry_context(on=on):
            with attempt:
                num_called += 1
                raise TypeError("passed")

    assert 1 == num_called
    assert 1 == attempt.num


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
            SimpleNamespace(
                attempt_number=i,
                outcome=SimpleNamespace(exception=ValueError),
            )
        )
        assert jittered <= 0.42


def test_backoff_no_overflow_on_high_attempt_numbers():
    """
    Exponential backoff with a float base does not raise OverflowError when
    the attempt number exceeds 1024.

    Regression test for https://github.com/hynek/stamina/issues/104.
    """
    rci = stamina.retry_context(
        on=ValueError, wait_max=5.0, attempts=None, timeout=None
    )

    for num in (1025, 2000, 10_000):
        backoff = rci._backoff_for_attempt_number(num)

        assert 5.0 == backoff

        jittered = rci._jittered_backoff_for_rcs(
            SimpleNamespace(
                attempt_number=num,
                outcome=SimpleNamespace(exception=ValueError),
            )
        )

        assert jittered <= 5.0


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


class CustomBackoffError(Exception):
    def __init__(self, backoff: float):
        self.backoff = backoff
        super().__init__(f"Retry after {backoff}s")


class TestBackoffHookSync:
    def test_backoff_hook_in_test_mode_returns_zero(self):
        """
        In test mode, custom backoffs are ignored.
        """
        attempts = 0

        with stamina.set_testing(True, attempts=3):

            @stamina.retry(on=lambda exc: 10.0, attempts=3)
            def f():
                nonlocal attempts
                attempts += 1
                if attempts < 3:
                    raise ValueError("retry")
                return 42

            start = time.perf_counter()
            result = f()
            duration = time.perf_counter() - start

        assert 42 == result
        assert 3 == attempts
        assert duration < 0.1

    def test_backoff_hook_returns_float(self):
        """
        If a backoff hook returns a float, it is used as the backoff duration.
        """
        attempts = 0

        @stamina.retry(on=lambda exc: 0.0, wait_initial=5, attempts=3)
        def f():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("retry")
            return 42

        started_at = time.perf_counter()
        result = f()
        duration = time.perf_counter() - started_at

        assert 42 == result
        assert 3 == attempts
        assert duration < 5

    def test_backoff_hook_returns_timedelta(self):
        """
        If a backoff hook returns a timedelta, it is used as the backoff duration.
        """
        attempts = 0

        @stamina.retry(
            on=lambda exc: dt.timedelta(seconds=0), wait_initial=5, attempts=3
        )
        def f():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("retry")
            return 42

        started_at = time.perf_counter()
        result = f()
        duration = time.perf_counter() - started_at

        assert 42 == result
        assert 2 == attempts
        assert duration < 1

    def test_backoff_hook_custom_backoff_from_exception(self):
        """
        A backoff hook can extract a custombackoff from exception attributes.
        """
        attempts = 0

        def hook(exc):
            if isinstance(exc, CustomBackoffError):
                return exc.backoff
            return False

        @stamina.retry(on=hook, attempts=3, wait_initial=5)
        def f():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise CustomBackoffError(0)

            return 42

        started_at = time.perf_counter()
        result = f()
        duration = time.perf_counter() - started_at

        assert 42 == result
        assert 2 == attempts
        assert duration < 5

    def test_backoff_hook_with_retry_context(self):
        """
        Backoff hooks work with retry_context.
        """
        attempts = 0

        started_at = time.perf_counter()
        for attempt in stamina.retry_context(
            on=lambda exc: 0.0, wait_initial=5, attempts=3
        ):
            with attempt:
                attempts += 1
                if attempts < 2:
                    raise ValueError("retry")

        duration = time.perf_counter() - started_at

        assert 2 == attempts
        assert duration < 5

    def test_backoff_hook_returns_none(self):
        """
        If a backoff hook returns None, it is treated as False and a warning is
        raised.
        """

        @stamina.retry(on=lambda exc: None, attempts=3)
        def f():
            raise ValueError("retry")

        with pytest.raises(ValueError), pytest.warns() as ws:
            f()

        msg = ws.pop().message.args[0]

        assert "Backoff hook" in msg
        assert "lambda" in msg
