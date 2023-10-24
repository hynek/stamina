# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from threading import Lock
from typing import Iterable

from ._instrumentation import get_default_hooks
from .typing import RetryHook


class _Config:
    """
    Global stamina configuration.

    Strictly private.
    """

    __slots__ = ("lock", "is_active", "_on_retry", "_get_on_retry")

    lock: Lock
    is_active: bool
    _on_retry: Iterable[RetryHook]

    def __init__(self, lock: Lock) -> None:
        self.lock = lock
        self.is_active = True

        # Prepare delayed initialization.
        self._on_retry = ()
        self._get_on_retry = self._init_on_first_retry

    @property
    def on_retry(self) -> Iterable[RetryHook]:
        return self._get_on_retry()

    def _init_on_first_retry(self) -> Iterable[RetryHook]:
        """
        Perform delayed initialization of on_retry hooks.
        """
        with self.lock:
            # Ensure hooks didn't init while waiting for the lock.
            if self._get_on_retry == self._init_on_first_retry:
                self._on_retry = get_default_hooks()
                self._get_on_retry = lambda: self._on_retry

        return self._on_retry


_LOCK = Lock()
_CONFIG = _Config(_LOCK)


def is_active() -> bool:
    """
    Check whether retrying is active.

    Returns:
        Whether retrying is active.
    """
    return _CONFIG.is_active


def set_active(active: bool) -> None:
    """
    Activate or deactivate retrying.

    Is idempotent and can be called repeatedly with the same value.
    """
    with _LOCK:
        _CONFIG.is_active = bool(active)
