# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from typing import Any, Protocol


class RetryHook(Protocol):
    """
    A callable that gets called after an attempt has failed and a retry has
    been scheduled.
    """

    def __call__(
        self,
        attempt: int,
        backoff: float,
        exc: Exception,
        name: str,
        args: Any,
        kwargs: Any,
    ) -> None:
        ...
