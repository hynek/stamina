# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

import stamina

from stamina.instrumentation import (
    RetryHookFactory,
    get_on_retry_hooks,
    set_on_retry_hooks,
)
from stamina.instrumentation._data import guess_name
from stamina.instrumentation._hooks import get_default_hooks
from stamina.instrumentation._structlog import init_structlog


try:
    import structlog
except ImportError:
    structlog = None

try:
    import prometheus_client
except ImportError:
    prometheus_client = None


def function():
    pass


async def async_function():
    pass


class Foo:
    def method(self):
        pass

    async def async_method(self):
        pass


foo = Foo()


class TestGuessName:
    @pytest.mark.parametrize(
        ("obj", "name"),
        [
            (function, "test_instrumentation.function"),
            (async_function, "test_instrumentation.async_function"),
            (foo.method, "test_instrumentation.Foo.method"),
            (foo.async_method, "test_instrumentation.Foo.async_method"),
            (Foo.method, "test_instrumentation.Foo.method"),
            (Foo.async_method, "test_instrumentation.Foo.async_method"),
        ],
    )
    def test_module_scope(self, obj, name):
        """
        Names of callables are guessed.
        """
        assert f"tests.{name}" == guess_name(obj)

    def test_local(self):
        """
        Scope-local functions are guessed.
        """

        def f():
            pass

        async def async_f():
            pass

        assert (
            "tests.test_instrumentation.TestGuessName.test_local.<locals>.f"
            == guess_name(f)
        )
        assert (
            "tests.test_instrumentation.TestGuessName.test_local.<locals>.async_f"
            == guess_name(async_f)
        )


def test_get_default_hooks():
    """
    Both default instrumentations are detected.
    """
    if prometheus_client:
        assert 2 == len(get_default_hooks())
    else:
        assert 1 == len(get_default_hooks())


def test_get_prometheus_counter():
    """
    Returns finalized counter if active.
    """
    counter = stamina.instrumentation.get_prometheus_counter()

    if prometheus_client:
        assert counter is not None
    else:
        assert counter is None


@pytest.mark.skipif(not structlog, reason="needs structlog")
def test_structlog_detected():
    """
    If structlog is importable, init_structlog returns a callable.
    """
    assert init_structlog()


@pytest.mark.skipif(structlog, reason="needs missing structlog")
class TestLogging:
    def test_sync(self, caplog):
        """
        Sync retries are logged.
        """

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        def f():
            raise ValueError

        with pytest.raises(ValueError):
            f()

        assert [
            ("stamina", 30, "stamina.retry_scheduled")
        ] == caplog.record_tuples

    async def test_async(self, caplog):
        """
        Async retries are logged.
        """

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        async def f():
            raise ValueError

        with pytest.raises(ValueError):
            await f()

        assert [
            ("stamina", 30, "stamina.retry_scheduled")
        ] == caplog.record_tuples


class TestSetOnRetryHooks:
    def test_none_is_default(self):
        """
        None is replaced with default hooks.
        """
        assert get_on_retry_hooks() is not None
        assert () != get_on_retry_hooks()

        set_on_retry_hooks(())

        assert () == get_on_retry_hooks()

        set_on_retry_hooks(None)

        assert () != get_on_retry_hooks()
        assert get_on_retry_hooks() is not None

    def test_init_hooks(self):
        """
        If a hook is wrapped in RetryHookFactory, init_hooks transforms it into
        a RetryHook. Otherwise it's left alone.
        """

        def hook(details):
            pass

        def delayed_hook(details):
            pass

        def init():
            return delayed_hook

        set_on_retry_hooks([hook, RetryHookFactory(init)])

        assert (
            hook,
            delayed_hook,
        ) == get_on_retry_hooks()
