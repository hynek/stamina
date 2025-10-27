# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from contextlib import contextmanager

import pytest

from dirty_equals import IsInstance

import stamina

from stamina.instrumentation import (
    RetryHookFactory,
    get_on_retry_hooks,
    set_on_retry_hooks,
)
from stamina.instrumentation._data import RetryDetails, guess_name
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

    @pytest.mark.anyio
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

    def test_sync_generator_function(self, caplog):
        """
        Sync generator function retries are logged.
        """

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        def f():
            yield
            raise ValueError

        with pytest.raises(ValueError):
            for _ in f():
                pass

        assert [
            ("stamina", 30, "stamina.retry_scheduled")
        ] == caplog.record_tuples

    @pytest.mark.anyio
    async def test_async_generator_function(self, caplog):
        """
        Async generator function retries are logged.
        """

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        async def f():
            yield
            raise ValueError

        with pytest.raises(ValueError):
            async for _ in f():
                pass

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

    def test_context_manager_hooks(self):
        """
        If a hook is a context manager, it's entered before retries start and exited
        after they finish.
        """
        entered = False
        exited = False
        deets = []

        @contextmanager
        def cm1(details):
            nonlocal entered
            entered = True

            deets.append(details)
            yield

            nonlocal exited
            exited = True

        class CM:
            def __init__(self):
                self.entered = False
                self.exited = False
                self.deets = []

            def __call__(self, details):
                self.deets.append(details)
                return self

            def __enter__(self):
                self.entered = True

            def __exit__(self, *_):
                self.exited = True

        cm2 = CM()

        set_on_retry_hooks([cm1, cm2])

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        def f():
            raise ValueError

        with pytest.raises(ValueError):
            f()

        assert entered
        assert exited
        assert cm2.entered
        assert cm2.exited

        assert (
            [
                RetryDetails(
                    name="tests.test_instrumentation.TestSetOnRetryHooks.test_context_manager_hooks.<locals>.f",
                    args=(),
                    kwargs={},
                    retry_num=1,
                    wait_for=0.0,
                    waited_so_far=0.0,
                    caused_by=IsInstance(ValueError),
                )
            ]
            == cm2.deets
            == deets
        )

    @pytest.mark.anyio
    async def test_context_manager_hooks_async(self):
        """
        Context manager hooks work with async functions too.
        """
        entered = False
        exited = False
        deets = []

        @contextmanager
        def cm1(details):
            nonlocal entered
            entered = True

            deets.append(details)
            yield

            nonlocal exited
            exited = True

        class CM:
            def __init__(self):
                self.entered = False
                self.exited = False
                self.deets = []

            def __call__(self, details):
                self.deets.append(details)
                return self

            def __enter__(self):
                self.entered = True

            def __exit__(self, *_):
                self.exited = True

        cm2 = CM()

        set_on_retry_hooks([cm1, cm2])

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        async def f():
            raise ValueError

        with pytest.raises(ValueError):
            await f()

        assert entered
        assert exited
        assert cm2.entered
        assert cm2.exited

        assert (
            [
                RetryDetails(
                    name="tests.test_instrumentation.TestSetOnRetryHooks.test_context_manager_hooks_async.<locals>.f",
                    args=(),
                    kwargs={},
                    retry_num=1,
                    wait_for=0.0,
                    waited_so_far=0.0,
                    caused_by=IsInstance(ValueError),
                )
            ]
            == cm2.deets
            == deets
        )

    def test_context_manager_hooks_with_sync_generator_function(self):
        """
        Context manager hooks work with sync generator functions too.
        """
        entered = False
        exited = False
        deets = []

        @contextmanager
        def cm1(details):
            nonlocal entered
            entered = True

            deets.append(details)
            yield

            nonlocal exited
            exited = True

        class CM:
            def __init__(self):
                self.entered = False
                self.exited = False
                self.deets = []

            def __call__(self, details):
                self.deets.append(details)
                return self

            def __enter__(self):
                self.entered = True

            def __exit__(self, *_):
                self.exited = True

        cm2 = CM()

        set_on_retry_hooks([cm1, cm2])

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        def f():
            yield
            raise ValueError

        with pytest.raises(ValueError):
            for _ in f():
                pass

        assert entered
        assert exited
        assert cm2.entered
        assert cm2.exited

        assert (
            [
                RetryDetails(
                    name="tests.test_instrumentation.TestSetOnRetryHooks.test_context_manager_hooks_with_sync_generator_function.<locals>.f",
                    args=(),
                    kwargs={},
                    retry_num=1,
                    wait_for=0.0,
                    waited_so_far=0.0,
                    caused_by=IsInstance(ValueError),
                )
            ]
            == cm2.deets
            == deets
        )

    @pytest.mark.anyio
    async def test_context_manager_hooks_with_async_generator_function(self):
        """
        Context manager hooks work with async generator functions too.
        """
        entered = False
        exited = False
        deets = []

        @contextmanager
        def cm1(details):
            nonlocal entered
            entered = True

            deets.append(details)
            yield

            nonlocal exited
            exited = True

        class CM:
            def __init__(self):
                self.entered = False
                self.exited = False
                self.deets = []

            def __call__(self, details):
                self.deets.append(details)
                return self

            def __enter__(self):
                self.entered = True

            def __exit__(self, *_):
                self.exited = True

        cm2 = CM()

        set_on_retry_hooks([cm1, cm2])

        @stamina.retry(on=ValueError, wait_max=0, attempts=2)
        async def f():
            yield
            raise ValueError

        with pytest.raises(ValueError):
            async for _ in f():
                pass

        assert entered
        assert exited
        assert cm2.entered
        assert cm2.exited

        assert (
            [
                RetryDetails(
                    name="tests.test_instrumentation.TestSetOnRetryHooks.test_context_manager_hooks_with_async_generator_function.<locals>.f",
                    args=(),
                    kwargs={},
                    retry_num=1,
                    wait_for=0.0,
                    waited_so_far=0.0,
                    caused_by=IsInstance(ValueError),
                )
            ]
            == cm2.deets
            == deets
        )
