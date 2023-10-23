# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from threading import Lock

from stamina import is_active, set_active
from stamina._config import _Config


def test_activate_deactivate():
    """
    set_active and is_active control/inspect _Active._is_active.
    """
    assert is_active()

    set_active(False)

    assert not is_active()

    set_active(True)

    assert is_active()


def test_config_init_concurrently():
    """
    Config._init_on_retry notices if the hooks have already been initialized
    (presumably while waiting for the lock).
    """
    cfg = _Config(Lock())

    def fake_on_retry(self):
        return self._on_retry

    cfg._get_on_retry = fake_on_retry
    cfg._on_retry = (1, 2)

    assert (1, 2) == cfg._init_on_retry()
    assert fake_on_retry is cfg._get_on_retry
