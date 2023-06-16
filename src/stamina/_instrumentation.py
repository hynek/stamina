# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations


try:
    import structlog

    logger = structlog.get_logger()
except ImportError:
    logger = None

try:
    from prometheus_client import Counter

    RETRY_COUNTER = Counter(
        "stamina_retries_total",
        "Total number of retries.",
        ("callable", "attempt", "error_type"),
    )
except ImportError:
    RETRY_COUNTER = None  # type: ignore[assignment]


def count_retries(
    attempt: int,
    backoff: float,
    exc: Exception,
    name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    """
    Count and log retries for callable *name*.
    """
    RETRY_COUNTER.labels(
        callable=name, attempt=attempt, error_type=guess_name(exc.__class__)
    ).inc()


def log_retries(
    attempt: int,
    backoff: float,
    exc: Exception,
    name: str,
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    logger.warning(
        "stamina.retry_scheduled",
        callable=name,
        attempt=attempt,
        backoff=backoff,
        error=repr(exc),
        args=tuple(repr(a) for a in args),
        kwargs=dict(kwargs.items()),
    )


INSTRUMENTS = []

if RETRY_COUNTER:
    INSTRUMENTS.append(count_retries)

if logger:
    INSTRUMENTS.append(log_retries)


def guess_name(obj: object) -> str:
    name = getattr(obj, "__qualname__", None) or "<unnamed object>"
    mod = getattr(obj, "__module__", None) or "<unknown module>"

    if mod == "builtins":
        return name

    return f"{mod}.{name}"
