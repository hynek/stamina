# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Iterable

from ._instrumentation import INSTRUMENTS
from .typing import RetryHook


@dataclass
class Config:
    is_active: bool
    on_retry: Iterable[RetryHook]


_CONFIG = Config(is_active=True, on_retry=INSTRUMENTS)
_LOCK = Lock()


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
