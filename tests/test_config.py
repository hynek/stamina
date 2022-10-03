# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from stamina import is_active, set_active


def test_activate_deactivate():
    """
    set_active and is_active control/inspect _Active._is_active.
    """
    assert is_active()

    set_active(False)

    assert not is_active()

    set_active(True)

    assert is_active()
