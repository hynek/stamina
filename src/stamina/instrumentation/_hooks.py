# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from ._data import RetryHook
from ._logging import init_logging
from ._structlog import init_structlog
from .prometheus import init_prometheus


def get_default_hooks() -> tuple[RetryHook, ...]:
    """
    Return the default hooks according to availability.
    """
    hooks = []

    if prom := init_prometheus():
        hooks.append(prom)

    hooks.append(init_structlog() or init_logging(30))

    return tuple(hooks)
