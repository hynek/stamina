# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RetryDetails:
    """
    Details about a retry attempt that are passed into :class:`RetryHook`s.
    """

    name: str
    attempt: int
    idle_for: float
    exception: Exception
    args: tuple[object, ...]
    kwargs: dict[str, object]


class RetryHook(Protocol):
    """
    A callable that gets called after an attempt has failed and a retry has
    been scheduled.
    """

    def __call__(self, details: RetryDetails) -> None:
        ...
