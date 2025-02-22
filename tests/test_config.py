# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from contextlib import suppress
from threading import Lock

from stamina import is_active, is_testing, set_active, set_testing
from stamina._config import CONFIG, _Config, _Testing


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

    assert (1, 2) == cfg._init_on_first_retry()
    assert fake_on_retry is cfg._get_on_retry


class TestTesting:
    def test_cap_true(self):
        """
        If cap is True, get_attempts returns the lower of the two values.
        """
        t = _Testing(2, True)

        assert 1 == t.get_attempts(1)
        assert 2 == t.get_attempts(3)

    def test_cap_false(self):
        """
        If cap is False, get_attempts always returns the testing value.
        """
        t = _Testing(2, False)

        assert 2 == t.get_attempts(1)
        assert 2 == t.get_attempts(3)

    def test_cap_true_with_none(self):
        """
        If cap is True and attempts is None, get_attempts returns the
        testing value.
        """
        t = _Testing(100, True)

        assert 100 == t.get_attempts(None)

    def test_context_manager(self):
        """
        set_testing works as a context manager.
        """
        assert not is_testing()

        with set_testing(True, attempts=3):
            assert is_testing()
            assert 3 == CONFIG.testing.get_attempts(None)
            assert not CONFIG.testing.cap

        assert not is_testing()

    def test_context_manager_nested(self):
        """
        set_testing context managers can be nested.
        """
        assert not is_testing()

        with set_testing(True, attempts=3):
            assert is_testing()
            assert CONFIG.testing.attempts == 3

            with set_testing(True, attempts=5, cap=True):
                assert is_testing()
                assert CONFIG.testing.attempts == 5
                assert CONFIG.testing.cap

            assert is_testing()
            assert CONFIG.testing.attempts == 3
            assert not CONFIG.testing.cap

        assert not is_testing()

    def test_context_manager_exception(self):
        """
        set_testing context manager restores state even if an exception occurs.
        """
        assert not is_testing()

        with suppress(ValueError), set_testing(True, attempts=3):
            assert is_testing()
            raise ValueError("test")

        assert not is_testing()
