# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from ._config import is_active, set_active
from ._core import retry, retry_context
from ._instrumentation import RETRY_COUNTER


__all__ = [
    "retry",
    "retry_context",
    "is_active",
    "set_active",
    "RETRY_COUNTER",
]


def __getattr__(name: str) -> str:
    if name != "__version__":
        msg = f"module {__name__} has no attribute {name}"
        raise AttributeError(msg)

    from importlib.metadata import metadata

    return metadata("stamina")["version"]
