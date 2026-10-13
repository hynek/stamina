# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime as dt


class TryAgain(Exception):  # noqa: N818 -- it's a signal, not an error
    """
    Raise this exception to force a retry, whatever *on* says.

    *attempts* and *timeout* still apply. When they don't allow another
    attempt, *stamina* raises the exception that you raised :class:`TryAgain`
    ``from``. Without one, the caller gets the :class:`TryAgain` itself.

    To keep :class:`TryAgain` out of your API, always raise it ``from`` an
    exception. Either the one you caught or a new one::

        try:
            resp = httpx2.get(url).raise_for_status()
        except httpx2.TimeoutException as e:
            raise TryAgain from e

        if resp.json()["status"] == "pending":
            raise TryAgain from JobStillPending()

    Note that a new exception, like ``JobStillPending()`` here, has no
    traceback until *stamina* raises it, so its traceback starts inside
    *stamina*.

    Args:
        after:
            Wait at least this long before the next attempt: a number of
            seconds, a :class:`datetime.timedelta`, or a timezone-aware
            :class:`datetime.datetime` to wait until. For example, from a
            `Retry-After
            <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After>`_
            header.

            *stamina* adds the usual jitter to it. If the regular backoff is
            longer, *stamina* uses the regular backoff. *wait_max* doesn't
            apply. A datetime in the past doesn't add any wait.

    Raises:
        TypeError: If *after* is a naive :class:`datetime.datetime`.

    .. versionadded:: 26.2.0
    """

    after: float | dt.timedelta | dt.datetime | None

    def __init__(
        self,
        *args: object,
        after: float | dt.timedelta | dt.datetime | None = None,
    ) -> None:
        if isinstance(after, dt.datetime) and after.utcoffset() is None:
            msg = "after must be a timezone-aware datetime."
            raise TypeError(msg)

        super().__init__(*args)

        self.after = after
