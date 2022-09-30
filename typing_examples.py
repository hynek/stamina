# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from stamina import is_active, retry, set_active


@retry(on=ValueError)
def just_exc() -> None:
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


set_active(False)

if is_active() is True:
    ...

set_active(False)
