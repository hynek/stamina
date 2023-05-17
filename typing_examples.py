# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any

from tenacity import RetryCallState

from stamina import is_active, retry, set_active


@retry(on=ValueError)
def just_exc() -> None:
    ...


@retry(on=TypeError)
async def just_exc_async() -> None:
    ...


@retry(on=TypeError, timeout=13.0)
def exc_timeout() -> None:
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


set_active(False)

if is_active() is True:
    ...

set_active(False)


def hook(
    retry_state: RetryCallState, name: str, args: Any, kwargs: Any
) -> None:
    return None
