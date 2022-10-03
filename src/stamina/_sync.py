# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import tenacity as _t

from ._config import _CONFIG
from ._instrumentation import guess_name


if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec


__all__ = ["retry"]


T = TypeVar("T")
P = ParamSpec("P")


def retry(
    *,
    on: type[Exception] | tuple[type[Exception], ...],
    attempts: int | None = 10,
    timeout: float | int | None = 45.0,
    wait_initial: float | int = 0.1,
    wait_max: float | int = 5.0,
    wait_jitter: float | int = 1.0,
    wait_exp_base: float | int = 2.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Retry if one of configured exceptions are raised.

    The backoff delays between retries grow exponentially plus a random jitter.

    Example:

        To retry three times HTTP errors keeping the rest at default::

            import httpx

            from stamina import retry

            @retry(on=httpx.HTTPError, attempts=3)
            def do_it(code: int) -> httpx.Response:
                resp = httpx.get(f"https://httpbin.org/status/{code}")
                resp.raise_for_status()

                return resp
    """
    retry_ = _t.retry_if_exception_type(on)
    wait = _t.wait_exponential_jitter(
        initial=wait_initial,
        max=wait_max,
        exp_base=wait_exp_base,
        jitter=wait_jitter,
    )
    stop = _make_stop(attempts=attempts, timeout=timeout)

    def retry_decorator(wrapped: Callable[P, T]) -> Callable[P, T]:
        name = guess_name(wrapped)

        @wraps(wrapped)
        def inner(*args: P.args, **kw: P.kwargs) -> T:
            if not _CONFIG.is_active:
                return wrapped(*args, **kw)

            before_sleep: Callable[[_t.RetryCallState], None] | None
            if _CONFIG.on_retry:

                def before_sleep(rcs: _t.RetryCallState) -> None:
                    attempt = rcs.attempt_number
                    exc = rcs.outcome.exception()
                    backoff = rcs.idle_for

                    for hook in _CONFIG.on_retry:
                        hook(
                            attempt=attempt,
                            backoff=backoff,
                            exc=exc,
                            name=name,
                            args=args,
                            kwargs=kw,
                        )

            else:
                before_sleep = None

            for attempt in _t.Retrying(
                retry=retry_,
                wait=wait,
                stop=stop,
                reraise=True,
                before_sleep=before_sleep,
            ):
                with attempt:
                    res = wrapped(*args, **kw)

            return res

        return inner

    return retry_decorator


def _make_stop(*, attempts: int | None, timeout: float | None) -> _t.stop_base:
    """
    Combine *attempts* and *timeout* into one stop condition.
    """
    stops = []

    if attempts:
        stops.append(_t.stop_after_attempt(attempts))
    if timeout:
        stops.append(_t.stop_after_delay(timeout))

    if len(stops) > 1:
        return _t.stop_any(*stops)

    if not stops:
        return _t.stop_never

    return stops[0]
