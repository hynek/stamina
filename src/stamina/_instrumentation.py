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

    .. versionadded:: 23.2.0
    """

    name: str
    args: tuple[object, ...]
    kwargs: dict[str, object]
    retry_num: int
    idle_for: float
    caused_by: Exception


class RetryHook(Protocol):
    """
    A callable that gets called after an attempt has failed and a retry has
    been scheduled.

    .. versionadded:: 23.2.0
    """

    def __call__(self, details: RetryDetails) -> None:
        ...


def get_default_hooks() -> tuple[RetryHook, ...]:
    """
    Return the default hooks according to availability.
    """
    hooks = []

    if prom := init_prometheus():
        hooks.append(prom)

    hooks.append(init_structlog() or init_logging(30))

    return tuple(hooks)


RETRY_COUNTER = None


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

    global RETRY_COUNTER  # noqa: PLW0603

    # Mostly for testing so we can call init_prometheus more than once.
    if RETRY_COUNTER is None:
        RETRY_COUNTER = Counter(
            "stamina_retries_total",
            "Total number of retries.",
            ("callable", "retry_num", "error_type"),
        )

    def count_retries(details: RetryDetails) -> None:
        """
        Count and log retries for callable *name*.
        """
        RETRY_COUNTER.labels(
            callable=details.name,
            retry_num=details.retry_num,
            error_type=guess_name(details.caused_by.__class__),
        ).inc()

    return count_retries


def init_structlog() -> RetryHook | None:
    """
    Try to initialize structlog instrumentation.

    Return None if it's not available.

    .. versionadded:: 23.2.0
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
            args=tuple(repr(a) for a in details.args),
            kwargs=dict(details.kwargs.items()),
            retry_num=details.retry_num,
            caused_by=repr(details.caused_by),
            idle_for=details.idle_for,
        )

    return log_retries


def init_logging(log_level: int) -> RetryHook:
    """
    Initialize logging using the standard library.

    Returned hook logs scheduled retries at *log_level*.

    .. versionadded:: 23.2.0
    """
    import logging

    logger = logging.getLogger("stamina")

    def log_retries(details: RetryDetails) -> None:
        logger.log(
            log_level,
            "stamina.retry_scheduled",
            extra={
                "stamina.callable": details.name,
                "stamina.args": tuple(repr(a) for a in details.args),
                "stamina.kwargs": dict(details.kwargs.items()),
                "stamina.retry_num": details.retry_num,
                "stamina.caused_by": repr(details.caused_by),
                "stamina.idle_for": details.idle_for,
            },
        )

    return log_retries


def guess_name(obj: object) -> str:
    name = getattr(obj, "__qualname__", None) or "<unnamed object>"
    mod = getattr(obj, "__module__", None) or "<unknown module>"

    if mod == "builtins":
        return name

    return f"{mod}.{name}"
