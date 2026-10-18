# SPDX-FileCopyrightText: 2026 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

"""
Benchmarks for synchronous retries.

All waits are set to zero so we measure stamina's (and Tenacity's) overhead
instead of sleeping.
"""

import pytest

import stamina


NO_WAIT = {"wait_initial": 0, "wait_max": 0, "wait_jitter": 0}
CALLS = 100
FAILURES = 5


class Flaky:
    """
    Callable that fails *failures* times before succeeding, then resets.
    """

    def __init__(self, failures):
        self.failures = failures
        self.left = failures

    def __call__(self):
        if self.left:
            self.left -= 1
            raise ValueError

        self.left = self.failures

        return 42


def test_decorator_success(benchmark):
    """
    Decorated function that succeeds on the first attempt.
    """

    @stamina.retry(on=ValueError, **NO_WAIT)
    def f():
        return 42

    @benchmark
    def _():
        for _ in range(CALLS):
            f()


def test_decorator_retries(benchmark):
    """
    Decorated function that fails a few times before succeeding.
    """
    f = stamina.retry(on=ValueError, **NO_WAIT)(Flaky(FAILURES))

    @benchmark
    def _():
        for _ in range(CALLS):
            f()


def test_decorator_backoff_hook_retries(benchmark):
    """
    Retries decided by a backoff hook instead of an exception type.
    """
    f = stamina.retry(
        on=lambda exc: isinstance(exc, ValueError) and 0.0, **NO_WAIT
    )(Flaky(FAILURES))

    @benchmark
    def _():
        for _ in range(CALLS):
            f()


def test_decorator_retries_with_hook(benchmark):
    """
    Retries with a custom on-retry hook so RetryDetails get built and
    dispatched.
    """
    details = []
    stamina.instrumentation.set_on_retry_hooks([details.append])
    f = stamina.retry(on=ValueError, **NO_WAIT)(Flaky(FAILURES))

    @benchmark
    def _():
        for _ in range(CALLS):
            f()
        details.clear()


def test_decorator_inactive(benchmark):
    """
    Calls while retries are globally deactivated.
    """
    stamina.set_active(False)

    @stamina.retry(on=ValueError, **NO_WAIT)
    def f():
        return 42

    @benchmark
    def _():
        for _ in range(CALLS):
            f()


def test_decorator_testing_mode(benchmark):
    """
    Retries while in testing mode.
    """
    stamina.set_testing(True, attempts=FAILURES + 1)
    f = stamina.retry(on=ValueError)(Flaky(FAILURES))

    @benchmark
    def _():
        for _ in range(CALLS):
            f()

    stamina.set_testing(False)


def test_decorate(benchmark):
    """
    Applying the decorator to a function.
    """

    def f():
        return 42

    @benchmark
    def _():
        for _ in range(CALLS):
            stamina.retry(on=ValueError)(f)


def test_retry_context_success(benchmark):
    """
    retry_context block that succeeds on the first attempt.
    """

    @benchmark
    def _():
        for _ in range(CALLS):
            for attempt in stamina.retry_context(on=ValueError, **NO_WAIT):
                with attempt:
                    pass


def test_retry_context_retries(benchmark):
    """
    retry_context block that fails a few times before succeeding.
    """
    f = Flaky(FAILURES)

    @benchmark
    def _():
        for _ in range(CALLS):
            for attempt in stamina.retry_context(on=ValueError, **NO_WAIT):
                with attempt:
                    f()


@pytest.mark.parametrize("bound", [False, True], ids=["unbound", "bound"])
def test_retrying_caller(benchmark, bound):
    """
    RetryingCaller and BoundRetryingCaller with a flaky callable.
    """
    rc = stamina.RetryingCaller(**NO_WAIT)
    f = Flaky(FAILURES)

    if bound:
        brc = rc.on(ValueError)

        def call():
            return brc(f)

    else:

        def call():
            return rc(ValueError, f)

    @benchmark
    def _():
        for _ in range(CALLS):
            call()
