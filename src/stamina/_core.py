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
from types import TracebackType
from typing import AsyncIterator, Iterable, Iterator, TypeVar

import tenacity as _t

from stamina.typing import RetryHook

from ._config import _CONFIG
from ._instrumentation import guess_name


if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec


T = TypeVar("T")
P = ParamSpec("P")


def retry_context(
    on: type[Exception] | tuple[type[Exception], ...],
    attempts: int | None = 10,
    timeout: float | dt.timedelta | None = 45.0,
    wait_initial: float | dt.timedelta = 0.1,
    wait_max: float | dt.timedelta = 5.0,
    wait_jitter: float | dt.timedelta = 1.0,
    wait_exp_base: float = 2.0,
) -> _RetryContextIterator:
    """
    Iterator that yields context managers that can be used to retry code
    blocks.

    Arguments have the same meaning as for :func:`stamina.retry`.

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
class Attempt:
    """
    A context manager that can be used to retry code blocks.

    Instances are yielded by the :func:`stamina.retry_context` iterator.

    .. versionadded:: 23.2.0
    """

    _t_attempt: _t.AttemptManager

    @property
    def num(self) -> int:
        """
        The number of the current attempt.
        """
        return self._t_attempt.retry_state.attempt_number  # type: ignore[no-any-return]

    def __enter__(self) -> None:
        return self._t_attempt.__enter__()  # type: ignore[no-any-return]

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return self._t_attempt.__exit__(  # type: ignore[no-any-return]
            exc_type, exc_value, traceback
        )


_STOP_NO_RETRY = _t.stop_after_attempt(1)


class _LazyNoAsyncRetry:
    """
    Allows us a free null object pattern using non-retries and avoid None.
    """

    def __aiter__(self) -> _t.AsyncRetrying:
        return _t.AsyncRetrying(reraise=True, stop=_STOP_NO_RETRY).__aiter__()


_LAZY_NO_ASYNC_RETRY = _LazyNoAsyncRetry()


@dataclass
class _RetryContextIterator:
    __slots__ = ("_t_kw", "_t_a_retrying", "_name", "_args", "_kw")
    _t_kw: dict[str, object]
    _t_a_retrying: _t.AsyncRetrying
    _name: str
    _args: tuple[object, ...]
    _kw: dict[str, object]

    @classmethod
    def from_params(
        cls,
        on: type[Exception] | tuple[type[Exception], ...],
        attempts: int | None,
        timeout: float | dt.timedelta | None,
        wait_initial: float | dt.timedelta,
        wait_max: float | dt.timedelta,
        wait_jitter: float | dt.timedelta,
        wait_exp_base: float,
        name: str,
        args: tuple[object, ...],
        kw: dict[str, object],
    ) -> _RetryContextIterator:
        return cls(
            _name=name,
            _args=args,
            _kw=kw,
            _t_kw={
                "retry": _t.retry_if_exception_type(on),
                "wait": _t.wait_exponential_jitter(
                    initial=wait_initial.total_seconds()
                    if isinstance(wait_initial, dt.timedelta)
                    else wait_initial,
                    max=wait_max.total_seconds()
                    if isinstance(wait_max, dt.timedelta)
                    else wait_max,
                    exp_base=wait_exp_base,
                    jitter=wait_jitter.total_seconds()
                    if isinstance(wait_jitter, dt.timedelta)
                    else wait_jitter,
                ),
                "stop": _make_stop(
                    attempts=attempts,
                    timeout=timeout.total_seconds()
                    if isinstance(timeout, dt.timedelta)
                    else timeout,
                ),
                "reraise": True,
            },
            _t_a_retrying=_LAZY_NO_ASYNC_RETRY,
        )

    def with_name(
        self, name: str, args: tuple[object, ...], kw: dict[str, object]
    ) -> _RetryContextIterator:
        """
        Recreate ourselves with a new name and arguments.
        """
        return replace(self, _name=name, _args=args, _kw=kw)

    def __iter__(self) -> Iterator[Attempt]:
        if not _CONFIG.is_active:
            for r in _t.Retrying(
                reraise=True, stop=_STOP_NO_RETRY
            ):  # pragma: no cover -- it's always once + GeneratorExit
                yield Attempt(r)

        for r in _t.Retrying(
            before_sleep=_make_before_sleep(
                self._name, _CONFIG.on_retry, self._args, self._kw
            )
            if _CONFIG.on_retry
            else None,
            **self._t_kw,
        ):
            yield Attempt(r)

    def __aiter__(self) -> AsyncIterator[Attempt]:
        if _CONFIG.is_active:
            self._t_a_retrying = _t.AsyncRetrying(
                before_sleep=_make_before_sleep(
                    self._name, _CONFIG.on_retry, self._args, self._kw
                )
                if _CONFIG.on_retry
                else None,
                **self._t_kw,
            )

        self._t_a_retrying = self._t_a_retrying.__aiter__()

        return self

    async def __anext__(self) -> Attempt:
        return Attempt(await self._t_a_retrying.__anext__())


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


def retry(
    *,
    on: type[Exception] | tuple[type[Exception], ...],
    attempts: int | None = 10,
    timeout: float | dt.timedelta | None = 45.0,
    wait_initial: float | dt.timedelta = 0.1,
    wait_max: float | dt.timedelta = 5.0,
    wait_jitter: float | dt.timedelta = 1.0,
    wait_exp_base: float = 2.0,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    r"""
    Retry if one of configured exceptions are raised.

    The backoff delays between retries grow exponentially plus a random jitter.

    The backoff for retry attempt number *attempt* is computed as:

    .. keep in-sync with docs/motivation.md
    .. math::

       wait\_initial * wait\_exp\_base^{attempt - 1} + random(0, wait\_jitter)

    Since :math:`x^0` is always 1, the first backoff is within the interval
    :math:`[wait\_initial,wait\_initial+wait\_jitter]`. Thus, with default
    values between 0.1 and 1.1 seconds.

    If all retries fail, the *last* exception is let through.

    All float-based time parameters are in seconds.

    Parameters:
        on: An Exception or a tuple of Exceptions on which the decorated
            callable will be retried. There is no default -- you *must* pass
            this explicitly.

        attempts: Maximum total number of attempts. Can be combined with
            *timeout*.

        timeout: Maximum total time for all retries. Can be combined with
            *attempts*.

        wait_initial: Minimum backoff before the *first* retry.

        wait_max: Maximum backoff time between retries at any time.

        wait_jitter: Maximum *jitter* that is added to retry back-off delays
            (the actual jitter added is a random number between 0 and
            *wait_jitter*)

        wait_exp_base: The exponential base used to compute the retry backoff.

    .. versionchanged:: 23.1.0

       All time-related parameters can now be specified as a
       :class:`datetime.timedelta`.
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
                    return await wrapped(*args, **kw)  # type: ignore[no-any-return]

        return async_inner  # type: ignore[return-value]

    return retry_decorator
