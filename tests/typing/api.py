# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

"""
This file is used to test the type annotations of the public API. It is NOT
meant to be executed.
"""

from __future__ import annotations

import datetime as dt

from stamina import (
    AsyncRetryingCaller,
    BoundAsyncRetryingCaller,
    BoundRetryingCaller,
    RetryingCaller,
    is_active,
    is_testing,
    retry,
    retry_context,
    set_active,
    set_testing,
)
from stamina.instrumentation import (
    RetryDetails,
    RetryHook,
    RetryHookFactory,
    get_on_retry_hooks,
    set_on_retry_hooks,
)


@retry(on=ValueError)
def just_exc() -> None: ...


@retry(on=TypeError)
async def just_exc_async() -> None: ...


@retry(on=TypeError, timeout=13.0)
def exc_timeout() -> None: ...


@retry(on=TypeError, timeout=dt.timedelta(seconds=13.0))
def exc_timeout_timedelta() -> None: ...


@retry(on=TypeError, timeout=13.0, attempts=10)
def exc_timeout_attempts() -> None: ...


@retry(on=TypeError, timeout=None, attempts=None)
def exc_timeout_attempts_none() -> None: ...


@retry(
    on=TypeError,
    wait_initial=0.3,
    wait_max=1.0,
    wait_jitter=1.0,
    wait_exp_base=2.0,
)
def exc_tune_waiting() -> None: ...


@retry(
    on=TypeError,
    wait_initial=1,
    wait_max=2,
    wait_jitter=3,
    wait_exp_base=4,
)
def exc_tune_waiting_ints() -> None: ...


one_sec = dt.timedelta(seconds=1.0)


@retry(
    on=TypeError,
    timeout=one_sec,
    wait_initial=one_sec,
    wait_max=one_sec,
    wait_jitter=one_sec,
)
def exc_tune_waiting_timedelta() -> None: ...


set_active(False)

if is_active() is True:
    ...

set_active(False)

set_testing(True)
set_testing(True, attempts=2)

if is_testing() is False:
    ...

set_testing(False)


def hook(details: RetryDetails) -> None:
    return None


def init() -> RetryHook:
    return hook


set_on_retry_hooks([hook, RetryHookFactory(init)])

hooks: tuple[RetryHook, ...] = get_on_retry_hooks()


for attempt in retry_context(on=ValueError, timeout=13):
    with attempt:
        x: int = attempt.num
        y: float = attempt.next_wait

for attempt in retry_context(
    on=ValueError, timeout=dt.timedelta(seconds=13.0)
):
    with attempt:
        ...


async def f() -> None:
    async for attempt in retry_context(
        on=ValueError,
        timeout=one_sec,
        wait_initial=one_sec,
        wait_max=one_sec,
        wait_jitter=one_sec,
    ):
        with attempt:
            pass


def sync_f(x: int, foo: str) -> bool:
    return True


rc = RetryingCaller(timeout=13.0, attempts=10)

bound_rc: BoundRetryingCaller = rc.on(ValueError)

b: bool = rc(ValueError, sync_f, 1, foo="bar")
b = bound_rc(sync_f, 1, foo="bar")


async def async_f(x: int, foo: str) -> bool:
    return True


arc = AsyncRetryingCaller(timeout=13.0, attempts=10)
bound_arc: BoundAsyncRetryingCaller = arc.on(ValueError)


async def g() -> bool:
    global b  # noqa: PLW0603

    b = await arc(KeyError, async_f, 1, foo="bar")
    return await bound_arc(async_f, 1, foo="bar")
