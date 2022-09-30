# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import pytest

from stamina import set_active


@pytest.fixture(autouse=True)
def _activate():
    """
    Ensure we're active before each test.
    """
    set_active(True)
