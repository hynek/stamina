# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations


class _Active:
    _is_active: bool


_ACTIVE = _Active()
_ACTIVE._is_active = True


def is_active() -> bool:
    """
    Check whether retrying is active.

    .. warning::

        Please note that these APIs are **not** thread-safe and are **not**
        meant to be used in regular program flow. Their purposse is to speed up
        test suites.

    Returns:
        Whether retrying is active.
    """
    return _ACTIVE._is_active


def set_active(active: bool) -> None:
    """
    Activate or deactivate retrying.

    Is idempotent and can be called repeatedly with the same value.
    """
    _ACTIVE._is_active = bool(active)
