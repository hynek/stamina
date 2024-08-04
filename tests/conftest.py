# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import importlib.util

import pytest

import stamina._config


@pytest.fixture(autouse=True)
def _reset_config():
    """
    Ensure we're active and have default on-retry hooks before each test.
    """
    stamina.set_active(True)
    stamina.instrumentation.set_on_retry_hooks(None)


BACKENDS = [pytest.param(("asyncio", {}), id="asyncio")]
if importlib.util.find_spec("trio"):
    BACKENDS += [pytest.param(("trio", {}), id="trio")]


@pytest.fixture(params=BACKENDS)
def anyio_backend(request):
    return request.param


@pytest.fixture(
    name="on",
    params=[
        ValueError,
        (ValueError,),
        lambda exc: isinstance(exc, ValueError),
    ],
)
def _on(request):
    """
    Parametrize over different ways to specify the exception to retry on.
    """
    return request.param
