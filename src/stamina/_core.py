# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime as dt
import sys

from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import wraps
from inspect import iscoroutinefunction
from typing import Iterable, TypeVar

import tenacity as _t

from stamina.typing import RetryHook

from ._config import _CONFIG
from ._instrumentation import guess_name


if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec


__all__ = ["retry"]


T = TypeVar("T")
P = ParamSpec("P")


def retry_context(
    on: type[Exception] | tuple[type[Exception], ...],
    attempts: int | None = 10,
    timeout: float | dt.timedelta | dt.datetime | None = 45.0,
    wait_initial: float | dt.timedelta = 0.1,
    wait_max: float | dt.timedelta = 5.0,
    wait_jitter: float | dt.timedelta = 1.0,
    wait_exp_base: float = 2.0,
) -> _RetryContextIterator:
    """
    Iterator that yields context managers that can be used to retry code
    blocks.

    Arguments have the same meaning as for :func:`retry`.

    .. versionadded:: 23.1.0
    """

    return _RetryContextIterator.from_params(
        on=on,
        attempts=attempts,
        timeout=timeout,
        wait_initial=wait_initial,
        wait_max=wait_max,
        wait_jitter=wait_jitter,
        wait_exp_base=wait_exp_base,
        name="<context block>",
        args=(),
        kw={},
    )


@dataclass
class _RetryContextIterator:
    __slots__ = ("_tenacity_kw", "_name", "_args", "_kw")
    _tenacity_kw: dict[str, object]
    _name: str
    _args: tuple[object, ...]
    _kw: dict[str, object]

    @classmethod
    def from_params(
        cls,
        on: type[Exception] | tuple[type[Exception], ...],
        attempts: int | None,
        timeout: float | dt.timedelta | dt.datetime | None,
        wait_initial: float | dt.timedelta,
        wait_max: float | dt.timedelta,
        wait_jitter: float | dt.timedelta,
        wait_exp_base: float,
        name: str,
        args: tuple[object, ...],
        kw: dict[str, object],
    ) -> _RetryContextIterator:
        wait_initial = (
            wait_initial.total_seconds()
            if isinstance(wait_initial, dt.timedelta)
            else wait_initial
        )
        wait_max = (
            wait_max.total_seconds()
            if isinstance(wait_max, dt.timedelta)
            else wait_max
        )
        wait_jitter = (
            wait_jitter.total_seconds()
            if isinstance(wait_jitter, dt.timedelta)
            else wait_jitter
        )
        if isinstance(timeout, dt.datetime):
            timeout = _StopBefore(
                timeout, wait_initial, wait_exp_base, wait_jitter
            )
        elif isinstance(timeout, dt.timedelta):
            timeout = timeout.total_seconds()

        return cls(
            _name=name,
            _args=args,
            _kw=kw,
            _tenacity_kw={
                "retry": _t.retry_if_exception_type(on),
                "wait": _t.wait_exponential_jitter(
                    initial=wait_initial,
                    max=wait_max,
                    exp_base=wait_exp_base,
                    jitter=wait_jitter,
                ),
                "stop": _make_stop(
                    attempts=attempts,
                    timeout=timeout,
                ),
                "reraise": True,
            },
        )

    _STOP_NO_RETRY = _t.stop_after_attempt(1)

    def __iter__(self) -> _t.Retrying:
        if not _CONFIG.is_active:
            return _t.Retrying(
                reraise=True, stop=self._STOP_NO_RETRY
            ).__iter__()

        return _t.Retrying(
            before_sleep=_make_before_sleep(
                self._name, _CONFIG.on_retry, self._args, self._kw
            )
            if _CONFIG.on_retry
            else None,
            **self._tenacity_kw,
        ).__iter__()

    def __aiter__(self) -> _t.AsyncRetrying:
        if not _CONFIG.is_active:
            return _t.AsyncRetrying(
                reraise=True, stop=self._STOP_NO_RETRY
            ).__aiter__()

        return _t.AsyncRetrying(
            before_sleep=_make_before_sleep(
                self._name, _CONFIG.on_retry, self._args, self._kw
            )
            if _CONFIG.on_retry
            else None,
            **self._tenacity_kw,
        ).__aiter__()

    def with_name(
        self, name: str, args: tuple[object, ...], kw: dict[str, object]
    ) -> _RetryContextIterator:
        """
        Recreate ourselves with a new name and arguments.
        """
        return replace(self, _name=name, _args=args, _kw=kw)


def _make_before_sleep(
    name: str,
    on_retry: Iterable[RetryHook],
    args: tuple[object, ...],
    kw: dict[str, object],
) -> Callable[[_t.RetryCallState], None]:
    """
    Create a `before_sleep` callback function that runs our `RetryHook`s with
    the necessary arguments.
    """

    def before_sleep(rcs: _t.RetryCallState) -> None:
        attempt = rcs.attempt_number
        exc = rcs.outcome.exception()
        idle_for = rcs.idle_for

        for hook in on_retry:
            hook(
                attempt=attempt,
                idle_for=idle_for,
                exc=exc,
                name=name,
                args=args,
                kwargs=kw,
            )

    return before_sleep


def _make_stop(
    *, attempts: int | None, timeout: float | _StopBefore | None
) -> _t.stop_base:
    """
    Combine *attempts* and *timeout* into one stop condition.
    """
    stops = []

    if attempts:
        stops.append(_t.stop_after_attempt(attempts))

    if timeout:
        if isinstance(timeout, _StopBefore):
            stops.append(timeout)
        else:
            stops.append(_t.stop_after_delay(timeout))

    if len(stops) > 1:
        return _t.stop_any(*stops)

    if not stops:
        return _t.stop_never

    return stops[0]


@dataclass
class _StopBefore(_t.stop.stop_base):  # type: ignore[misc]
    """
    Stop before a given timestamp.
    """

    __slots__ = ("deadline", "wait_initial", "wait_exp_base", "wait_jitter")

    deadline: dt.datetime
    wait_initial: float
    wait_exp_base: float
    wait_jitter: float

    def __call__(self, retry_state: _t.RetryCallState) -> bool:
        return (
            dt.datetime.now(tz=self.deadline.tzinfo)
            + dt.timedelta(
                # We don't have access to the next sleep, so we have to compute
                # the worst case.
                seconds=self.wait_initial
                * self.wait_exp_base**retry_state.attempt_number
                + self.wait_jitter
            )
            >= self.deadline
        )


def retry(
    *,
    on: type[Exception] | tuple[type[Exception], ...],
    attempts: int | None = 10,
    timeout: float | dt.timedelta | dt.datetime | None = 45.0,
    wait_initial: float | dt.timedelta = 0.1,
    wait_max: float | dt.timedelta = 5.0,
    wait_jitter: float | dt.timedelta = 1.0,
    wait_exp_base: float = 2.0,
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
    retry_ctx = _RetryContextIterator.from_params(
        on=on,
        attempts=attempts,
        timeout=timeout,
        wait_initial=wait_initial,
        wait_max=wait_max,
        wait_jitter=wait_jitter,
        wait_exp_base=wait_exp_base,
        name="<unknown>",
        args=(),
        kw={},
    )

    def retry_decorator(wrapped: Callable[P, T]) -> Callable[P, T]:
        name = guess_name(wrapped)

        if not iscoroutinefunction(wrapped):

            @wraps(wrapped)
            def sync_inner(*args: P.args, **kw: P.kwargs) -> T:  # type: ignore[return]
                for attempt in retry_ctx.with_name(  # noqa: RET503
                    name, args, kw
                ):
                    with attempt:
                        return wrapped(*args, **kw)

            return sync_inner

        @wraps(wrapped)
        async def async_inner(*args: P.args, **kw: P.kwargs) -> T:  # type: ignore[return]
            async for attempt in retry_ctx.with_name(  # noqa: RET503
                name, args, kw
            ):
                with attempt:
                    return await wrapped(*args, **kw)  # type: ignore[misc,no-any-return]

        return async_inner  # type: ignore[return-value]

    return retry_decorator
