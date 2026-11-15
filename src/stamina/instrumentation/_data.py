# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol


def guess_name(obj: object) -> str:
    name = getattr(obj, "__qualname__", None) or "<unnamed object>"
    mod = getattr(obj, "__module__", None) or "<unknown module>"

    if mod == "builtins":
        return name

    return f"{mod}.{name}"


@dataclass(frozen=True)
class RetryDetails:
    """
    Details about a retry attempt that are passed into
    [`RetryHook`][stamina.instrumentation.RetryHook]s.

    Attributes:
        name: Name of the callable that is being retried.

        args: Positional arguments that were passed to the callable.

        kwargs: Keyword arguments that were passed to the callable.

        retry_num:
            Number of the retry attempt. Starts at 1 after the first failure.

        wait_for:
            Time in seconds that *stamina* will wait before the next attempt.

        waited_so_far:
            Time in seconds that *stamina* has waited so far for the current
            callable.

        caused_by: Exception that caused the retry attempt.

    !!! caution
        **Modifying args or kwargs modifies the arguments of the next
        attempt.**

        *args* and *kwargs* are the same objects that *stamina* passes to the
        next attempt. If you change them or anything inside them, you change
        the arguments of the next attempt.

    !!! version-added "Added in 23.2.0"
    """

    __slots__ = (
        "args",
        "caused_by",
        "kwargs",
        "name",
        "retry_num",
        "wait_for",
        "waited_so_far",
    )

    name: str
    args: tuple[object, ...]
    kwargs: dict[str, object]
    retry_num: int
    wait_for: float
    waited_so_far: float
    caused_by: BaseException


class RetryHook(Protocol):
    """
    A callable that gets called after an attempt has failed and a retry has
    been scheduled.

    This is a [`typing.Protocol`][] that can be implemented by any callable
    that takes one argument of type
    [`RetryDetails`][stamina.instrumentation.RetryDetails] and returns None.

    If the hook returns a context manager, it will be entered when the retry is
    scheduled and exited right before the retry is attempted.

    For example:

    ```python
    def print_hook(details: stamina.instrumentation.RetryDetails) -> None:
        print("a retry has been scheduled!", details)

    stamina.instrumentation.set_on_retry_hooks([print_hook])
    ```

    !!! version-added "Added in 23.2.0"

    !!! version-added "Added in 25.1.0"
        Added support for context managers.
    """

    def __call__(
        self, details: RetryDetails
    ) -> AbstractContextManager[None] | None: ...


@dataclass(frozen=True)
class RetryHookFactory:
    """
    Wraps a callable that returns a
    [`RetryHook`][stamina.instrumentation.RetryHook].

    They are called on the first scheduled retry and can be used to delay
    initialization. If you need to pass arguments, you can do that using
    [`functools.partial()`][functools.partial].

    For example, if your instrumentation needs to import a module
    `something_expensive` which takes a long time to import, you can delay it
    until the first retry (or call to
    [`get_on_retry_hooks()`][stamina.instrumentation.get_on_retry_hooks]):

    ```python
    from stamina.instrumentation import RetryDetails, RetryHookFactory

    def init_with_expensive_import():
        import something_expensive

        def do_something(details: RetryDetails) -> None:
            something_expensive.do_something(details)

        return do_something

    stamina.instrumentation.set_on_retry_hooks(
        [RetryHookFactory(init_with_expensive_import)]
    )
    ```

    !!! version-added "Added in 23.2.0"
    """

    hook_factory: Callable[[], RetryHook]
