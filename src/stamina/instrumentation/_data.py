# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


def guess_name(obj: object) -> str:
    name = getattr(obj, "__qualname__", None) or "<unnamed object>"
    mod = getattr(obj, "__module__", None) or "<unknown module>"

    if mod == "builtins":
        return name

    return f"{mod}.{name}"


@dataclass(frozen=True)
class RetryDetails:
    r"""
    Details about a retry attempt that are passed into :class:`RetryHook`\ s.

    Attributes:
        name: Name of the callable that is being retried.

        args: Positional arguments that were passed to the callable.

        kwargs: Keyword arguments that were passed to the callable.

        retry_num: Number of the retry attempt. Starts at 1 after the first
            failure.

        wait_for: Time in seconds that *stamina* will wait before the next
            attempt.

        waited_so_far: Time in seconds that *stamina* has waited so far for the
            current callable.

        caused_by: Exception that caused the retry attempt.

    .. versionadded:: 23.2.0
    """

    __slots__ = (
        "name",
        "args",
        "kwargs",
        "retry_num",
        "wait_for",
        "waited_so_far",
        "caused_by",
    )

    name: str
    args: tuple[object, ...]
    kwargs: dict[str, object]
    retry_num: int
    wait_for: float
    waited_so_far: float
    caused_by: Exception


class RetryHook(Protocol):
    """
    A callable that gets called after an attempt has failed and a retry has
    been scheduled.

    This is a :class:`typing.Protocol` that can be implemented by any callable
    that takes one argument of type :class:`RetryDetails` and returns None.

    For example::

       def print_hook(details: stamina.instrumentation.RetryDetails) -> None:
           print("a retry has been scheduled!", details)

        stamina.set_on_retry_hooks([print_hook])

    .. versionadded:: 23.2.0
    """

    def __call__(self, details: RetryDetails) -> None:
        ...


@dataclass(frozen=True)
class RetryHookFactory:
    """
    Wraps a callable that returns a :class:`RetryHook`.

    They are called on the first scheduled retry and can be used to delay
    initialization.

    For example, if your instrumentation needs to import
    ``something_expensive`` which takes a long time to import, you can delay it
    until the first retry (or call to
    :func:`stamina.instrumentation.get_on_retry_hooks`)::

      from stamina.instrumentation import RetryHookFactory

       def init_with_expensive_import():
           import something_expensive

           def do_something(details: stamina.instrumentation.RetryDetails) -> None:
               something_expensive.do_something(details)

           return do_something


       stamina.set_on_retry_hooks([RetryHookFactory(init_with_expensive_import)])

    .. versionadded:: 23.2.0
    """

    hook_factory: Callable[[], RetryHook]
