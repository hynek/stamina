# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from . import instrumentation
from ._config import (
    is_active,
    set_active,
)
from ._core import Attempt, retry, retry_context


__all__ = [
    "Attempt",
    "retry",
    "retry_context",
    "is_active",
    "set_active",
    "instrumentation",
]


def __getattr__(name: str) -> str:
    if name != "__version__":
        msg = f"module {__name__} has no attribute {name}"
        raise AttributeError(msg)

    from importlib.metadata import version

    return version("stamina")
