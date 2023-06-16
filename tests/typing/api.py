# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

"""
This file is used to test the type annotations of the public API. It is NOT
meant to be executed.
"""

from __future__ import annotations

import datetime as dt

from tenacity import RetryCallState

from stamina import is_active, retry, retry_context, set_active


@retry(on=ValueError)
def just_exc() -> None:
    ...


@retry(on=TypeError)
async def just_exc_async() -> None:
    ...


@retry(on=TypeError, timeout=13.0)
def exc_timeout() -> None:
    ...


@retry(on=TypeError, timeout=dt.timedelta(seconds=13.0))
def exc_timeout_timedelta() -> None:
    ...


@retry(on=TypeError, timeout=dt.datetime.now(tz=dt.timezone.utc))
def exc_timeout_datetime() -> None:
    ...


@retry(on=TypeError, timeout=13.0, attempts=10)
def exc_timeout_attempts() -> None:
    ...


@retry(on=TypeError, timeout=None, attempts=None)
def exc_timeout_attempts_none() -> None:
    ...


@retry(
    on=TypeError,
    wait_initial=0.3,
    wait_max=1.0,
    wait_jitter=1.0,
    wait_exp_base=2.0,
)
def exc_tune_waiting() -> None:
    ...


@retry(
    on=TypeError,
    wait_initial=1,
    wait_max=2,
    wait_jitter=3,
    wait_exp_base=4,
)
def exc_tune_waiting_ints() -> None:
    ...


one_sec = dt.timedelta(seconds=1.0)


@retry(
    on=TypeError,
    timeout=one_sec,
    wait_initial=one_sec,
    wait_max=one_sec,
    wait_jitter=one_sec,
)
def exc_tune_waiting_timedelta() -> None:
    ...


set_active(False)

if is_active() is True:
    ...

set_active(False)


def hook(
    retry_state: RetryCallState, name: str, args: object, kwargs: object
) -> None:
    return None


for attempt in retry_context(on=ValueError, timeout=13):
    with attempt:
        ...

for attempt in retry_context(
    on=ValueError, timeout=dt.datetime.now(tz=dt.timezone.utc)
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
            ...
