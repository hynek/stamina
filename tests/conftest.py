# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import pytest

import stamina._config


@pytest.fixture(autouse=True)
def _reset_config():
    """
    Ensure we're active and have default on-retry hooks before each test.
    """
    stamina.set_active(True)
    stamina.instrumentation.set_on_retry_hooks(None)
