# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

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
    Details about a retry attempt that are passed into :class:`RetryHook`s.

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

    .. versionadded:: 23.2.0
    """

    def __call__(self, details: RetryDetails) -> None:
        ...
