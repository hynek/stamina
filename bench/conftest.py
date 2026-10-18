# SPDX-FileCopyrightText: 2026 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import asyncio
import time

import pytest

import stamina


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """
    Tenacity calls time.sleep(0) between attempts even if the backoff is zero.
    Replace it with a no-op so benchmarks aren't dominated by syscalls.
    """
    monkeypatch.setattr(time, "sleep", lambda _: None)


@pytest.fixture(autouse=True)
def _reset_config():
    """
    Ensure retries are active, not in testing mode, and have no on-retry hooks
    so benchmarks measure stamina's own overhead without logging noise.
    """
    stamina.set_active(True)
    stamina.set_testing(False)
    stamina.instrumentation.set_on_retry_hooks([])

    yield

    stamina.set_active(True)
    stamina.instrumentation.set_on_retry_hooks(None)


@pytest.fixture(name="run")
def _run():
    """
    Run a coroutine to completion on a long-lived event loop so the loop's
    setup cost doesn't dominate async benchmarks.
    """
    loop = asyncio.new_event_loop()

    yield loop.run_until_complete

    loop.close()
