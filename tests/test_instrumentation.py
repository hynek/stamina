# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

import stamina

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
