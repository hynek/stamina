# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

from stamina._instrumentation import guess_name


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
        "obj,name",
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
        assert name == guess_name(obj)

    def test_local(self):
        """
        Scope-local functions are guessed.
        """

        def f():
            pass

        async def async_f():
            pass

        assert (
            "test_instrumentation.TestGuessName.test_local.<locals>.f"
            == guess_name(f)
        )
        assert (
            "test_instrumentation.TestGuessName.test_local.<locals>.async_f"
            == guess_name(async_f)
        )
