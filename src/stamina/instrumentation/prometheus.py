# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from ._data import RetryDetails, RetryHook, guess_name


__all__ = ["RETRIES_TOTAL"]

RETRIES_TOTAL = None
"""
After initialization, this is the Prometheus `counter
<https://github.com/prometheus/client_python#counter>`_ that counts the number
of retries.

.. versionadded:: 23.2.0
"""


def init_prometheus() -> RetryHook | None:
    """
    Try to initialize Prometheus instrumentation.

    Return None if it's not available.

    .. versionadded:: 23.2.0
    """
    try:
        from prometheus_client import Counter
    except ImportError:
        return None

    global RETRIES_TOTAL  # noqa: PLW0603

    # Mostly for testing so we can call init_prometheus more than once.
    if RETRIES_TOTAL is None:
        RETRIES_TOTAL = Counter(
            "stamina_retries_total",
            "Total number of retries.",
            ("callable", "retry_num", "error_type"),
        )

    def count_retries(details: RetryDetails) -> None:
        """
        Count and log retries for callable *name*.
        """
        RETRIES_TOTAL.labels(
            callable=details.name,
            retry_num=details.retry_num,
            error_type=guess_name(details.caused_by.__class__),
        ).inc()

    return count_retries
