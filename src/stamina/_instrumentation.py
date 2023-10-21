# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from .typing import RetryDetails, RetryHook


def get_default_hooks() -> tuple[RetryHook, ...]:
    """
    Return the default hooks according to availability.
    """
    hooks = []

    if prom := init_prometheus():
        hooks.append(prom)

    if sl := init_structlog():
        hooks.append(sl)

    return tuple(hooks)


RETRY_COUNTER = None


def init_prometheus() -> RetryHook | None:
    """
    Try to initialize Prometheus instrumentation.

    Return None if it's not available.
    """
    try:
        from prometheus_client import Counter
    except ImportError:
        return None

    global RETRY_COUNTER  # noqa: PLW0603

    # Mostly for testing so we can call init_prometheus more than once.
    if RETRY_COUNTER is None:
        RETRY_COUNTER = Counter(
            "stamina_retries_total",
            "Total number of retries.",
            ("callable", "attempt", "error_type"),
        )

    def count_retries(details: RetryDetails) -> None:
        """
        Count and log retries for callable *name*.
        """
        RETRY_COUNTER.labels(
            callable=details.name,
            attempt=details.attempt,
            error_type=guess_name(details.exception.__class__),
        ).inc()

    return count_retries


def init_structlog() -> RetryHook | None:
    """
    Try to initialize structlog instrumentation.

    Return None if it's not available.
    """
    try:
        import structlog
    except ImportError:
        return None

    logger = structlog.get_logger()

    def log_retries(details: RetryDetails) -> None:
        logger.warning(
            "stamina.retry_scheduled",
            callable=details.name,
            attempt=details.attempt,
            slept=details.idle_for,
            error=repr(details.exception),
            args=tuple(repr(a) for a in details.args),
            kwargs=dict(details.kwargs.items()),
        )

    return log_retries


def guess_name(obj: object) -> str:
    name = getattr(obj, "__qualname__", None) or "<unnamed object>"
    mod = getattr(obj, "__module__", None) or "<unknown module>"

    if mod == "builtins":
        return name

    return f"{mod}.{name}"
