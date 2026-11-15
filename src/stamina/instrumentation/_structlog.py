# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from ._data import RetryDetails, RetryHook, RetryHookFactory


def init_structlog() -> RetryHook:
    """
    Initialize structlog instrumentation.

    !!! version-added "Added in 23.2.0"
    """
    import structlog

    logger = structlog.get_logger("stamina")

    def log_retries(details: RetryDetails) -> None:
        logger.warning(
            "stamina.retry_scheduled",
            callable=details.name,
            args=tuple(repr(a) for a in details.args),
            kwargs=dict(details.kwargs.items()),
            retry_num=details.retry_num,
            caused_by=repr(details.caused_by),
            wait_for=round(details.wait_for, 2),
            waited_so_far=round(details.waited_so_far, 2),
        )

    return log_retries


StructlogOnRetryHook = RetryHookFactory(init_structlog)
"""
Pass this object to
[`set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks] to
activate *structlog* integration.

Is active by default if *structlog* can be imported.

!!! info "See also"
    [*structlog*](instrumentation.md#structlog)

!!! version-added "Added in 23.2.0"
"""
