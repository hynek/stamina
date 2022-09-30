# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import sys

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import tenacity

from . import _control


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

    The back-off delays between retries grow exponentially plus a random
    jitter.

    Example:

        To retry three times HTTP errors keeping the rest at default::

            import httpx

            from stamina import retry

            @retry(on=httpx.HTTPError, attempts=3) def do_it(code: int) ->
            httpx.Response:
                resp = httpx.get(f"https://httpbin.org/status/{code}")
                resp.raise_for_status()

                return resp
    """
    retry_ = tenacity.retry_if_exception_type(on)
    wait = tenacity.wait_exponential_jitter(
        initial=wait_initial,
        max=wait_max,
        exp_base=wait_exp_base,
        jitter=wait_jitter,
    )
    stop = _make_stop(attempts=attempts, timeout=timeout)

    def retry_decorator(wrapped: Callable[P, T]) -> Callable[P, T]:
        @wraps(wrapped)
        def inner(*args: P.args, **kw: P.kwargs) -> T:
            if not _control._ACTIVE._is_active:
                return wrapped(*args, **kw)

            for attempt in tenacity.Retrying(
                retry=retry_, wait=wait, stop=stop, reraise=True
            ):
                with attempt:
                    res = wrapped(*args, **kw)

            return res

        return inner

    return retry_decorator


def _make_stop(
    *, attempts: int | None, timeout: float | None
) -> tenacity.stop_base:
    """
    Combine *attempts* and *timeout* into one stop condition.
    """
    stops = []

    if attempts:
        stops.append(tenacity.stop_after_attempt(attempts))
    if timeout:
        stops.append(tenacity.stop_after_delay(timeout))

    if not stops:
        return tenacity.stop_never

    if len(stops) > 1:
        return tenacity.stop_any(*stops)

    return stops[0]
