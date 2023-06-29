# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from importlib import metadata

import stamina


def test_version(recwarn):
    """
    stamina.__version__ returns the correct version and doesn't warn.
    """
    assert metadata.version("stamina") == stamina.__version__
    assert [] == recwarn.list
