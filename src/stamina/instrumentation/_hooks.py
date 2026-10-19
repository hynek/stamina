# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable, Iterable

from ._data import RetryDetails, RetryHook, RetryHookFactory
from ._logging import LoggingOnRetryHook
from ._prometheus import PrometheusOnRetryHook
from ._structlog import StructlogOnRetryHook


def init_hooks(
    maybe_delayed: tuple[RetryHook | RetryHookFactory, ...],
) -> tuple[RetryHook, ...]:
    """
    Execute delayed hook factories and return a tuple of finalized hooks.
    """
    hooks = []
    for hook_or_factory in maybe_delayed:
        if isinstance(hook_or_factory, RetryHookFactory):
            hooks.append(hook_or_factory.hook_factory())
        else:
            hooks.append(hook_or_factory)

    return tuple(hooks)


def get_default_hooks() -> tuple[RetryHookFactory, ...]:
    """
    Return the default hooks according to availability.
    """
    hooks = []

    try:
        import prometheus_client  # noqa: F401

        hooks.append(PrometheusOnRetryHook)
    except ImportError:
        pass

    try:
        import structlog  # noqa: F401

        hooks.append(StructlogOnRetryHook)
    except ImportError:
        hooks.append(LoggingOnRetryHook)

    return tuple(hooks)


def set_on_retry_hooks(
    hooks: Iterable[RetryHook | RetryHookFactory] | None,
) -> None:
    """
    Set hooks that are called after a retry has been scheduled.

    Args:
        hooks:
            Hooks to call after a retry has been scheduled. Passing None resets
            to default. To deactivate instrumentation, pass an empty iterable.

    .. versionadded:: 23.2.0
    """
    from .._config import CONFIG

    CONFIG.on_retry = tuple(hooks) if hooks is not None else hooks


def get_on_retry_hooks() -> tuple[RetryHook, ...]:
    """
    Get hooks that are called after a retry has been scheduled.

    Returns:
        Hooks that will run if a retry is scheduled. Factories are called if
        they haven't already.

    .. versionadded:: 23.2.0
    """
    from .._config import CONFIG

    return CONFIG.on_retry


def set_process_details(
    process_details: Callable[[RetryDetails], RetryDetails] | None,
) -> None:
    """
    Set a callable that processes :class:`RetryDetails` before *stamina*
    passes them to the retry hooks.

    *stamina* calls it once for each scheduled retry, before it calls the
    hooks. All hooks get the :class:`RetryDetails` that it returns. For
    example, you can use it to remove secrets from the arguments before they
    are logged.

    .. caution::

       **Modifying args or kwargs modifies the arguments of the next
       attempt.**

       *args* and *kwargs* are the same objects that *stamina* passes to the
       next attempt. If you change them or anything inside them, you change
       the arguments of the next attempt. Build new objects instead and put
       them into a new :class:`RetryDetails`, for example using
       :func:`dataclasses.replace`.

    Args:
        process_details:
            A callable that takes a :class:`RetryDetails` and returns a
            :class:`RetryDetails`. Passing None removes it.

    .. versionadded:: 26.2.0
    """
    from .._config import CONFIG

    CONFIG.process_details = process_details


def get_process_details() -> Callable[[RetryDetails], RetryDetails] | None:
    """
    Get the callable that processes :class:`RetryDetails` before *stamina*
    passes them to the retry hooks.

    Returns:
        The callable, or None if there is none.

    .. versionadded:: 26.2.0
    """
    from .._config import CONFIG

    return CONFIG.process_details
