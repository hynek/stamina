# SPDX-FileCopyrightText: 2026 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

"""
Benchmarks for asynchronous retries on asyncio.

All waits are set to zero so we measure stamina's (and Tenacity's) overhead
instead of sleeping.
"""

import stamina


NO_WAIT = {"wait_initial": 0, "wait_max": 0, "wait_jitter": 0}
CALLS = 100
FAILURES = 5


class AsyncFlaky:
    """
    Coroutine function that fails *failures* times before succeeding, then
    resets.
    """

    def __init__(self, failures):
        self.failures = failures
        self.left = failures

    async def __call__(self):
        if self.left:
            self.left -= 1
            raise ValueError

        self.left = self.failures

        return 42


def test_decorator_success(benchmark, run):
    """
    Decorated coroutine function that succeeds on the first attempt.
    """

    @stamina.retry(on=ValueError, **NO_WAIT)
    async def f():
        return 42

    async def calls():
        for _ in range(CALLS):
            await f()

    benchmark(lambda: run(calls()))


def test_decorator_retries(benchmark, run):
    """
    Decorated coroutine function that fails a few times before succeeding.
    """
    flaky = AsyncFlaky(FAILURES)

    @stamina.retry(on=ValueError, **NO_WAIT)
    async def f():
        return await flaky()

    async def calls():
        for _ in range(CALLS):
            await f()

    benchmark(lambda: run(calls()))


def test_retry_context_retries(benchmark, run):
    """
    async retry_context block that fails a few times before succeeding.
    """
    f = AsyncFlaky(FAILURES)

    async def calls():
        for _ in range(CALLS):
            async for attempt in stamina.retry_context(
                on=ValueError, **NO_WAIT
            ):
                with attempt:
                    await f()

    benchmark(lambda: run(calls()))


def test_async_retrying_caller(benchmark, run):
    """
    AsyncRetryingCaller with a flaky coroutine function.
    """
    rc = stamina.AsyncRetryingCaller(**NO_WAIT).on(ValueError)
    f = AsyncFlaky(FAILURES)

    async def calls():
        for _ in range(CALLS):
            await rc(f)

    benchmark(lambda: run(calls()))
