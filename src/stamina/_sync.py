# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import tenacity

from . import _control


__all__ = ["retry"]


T = TypeVar("T")
P = ParamSpec("P")


def retry(
    *,
    on: type[Exception] | tuple[type[Exception], ...],
    attempts: int | None = 10,
    timeout: float | None = 30.0,
    wait_initial: float = 0.2,
    wait_max: float = 5.0,
    wait_jitter: float = 1.0,
    wait_exp_base: float = 2.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Retry if one of configured exceptions are raised.

    The delays between retries grow exponentially plus a random jitter.

    Args:

        on: The Exception(s) that cause a retry. Every other is left through.
        attempts: Maximum number of attempts
        timeout: Maximum time the attempts may take

        wait_initial: Wait at least this long before first retry.

        wait_max: Don't wait longer than this between retries.

        wait_jitter: Maximum jitter added to retry delays.

        wait_exp_base: The retries are computed
            ``wait_exp_base**(attempt - 1) + random_jitter``.

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
