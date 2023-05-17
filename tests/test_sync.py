# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

import pytest
import tenacity

import stamina

from stamina._core import _make_stop


@pytest.mark.parametrize("attempts,timeout", [(None, 1), (1, None)])
def test_ok(attempts, timeout):
    """
    No error, no problem.
    """

    @stamina.retry(on=Exception, attempts=attempts, timeout=timeout)
    def f():
        return 42

    assert 42 == f()


def test_retries():
    """
    Retries if the specific error is raised.
    """
    i = 0

    @stamina.retry(on=ValueError, wait_max=0)
    def f():
        nonlocal i
        if i == 0:
            i += 1
            raise ValueError

        return 42

    assert 42 == f()
    assert 1 == i


def test_wrong_exception():
    """
    Exceptions that are not passed as `on` are left through.
    """

    @stamina.retry(on=ValueError)
    def f():
        raise TypeError("passed")

    with pytest.raises(TypeError, match="passed"):
        f()


def test_retry_inactive(monkeypatch):
    """
    If inactive, don't retry.
    """

    @stamina.retry(on=Exception)
    def f():
        raise Exception("passed")

    stamina.set_active(False)

    retrying = Mock()
    monkeypatch.setattr(stamina._core._t, "Retrying", retrying)

    with pytest.raises(Exception, match="passed"):
        f()

    retrying.assert_not_called()


class TestMakeStop:
    def test_never(self):
        """
        If all conditions are None, return stop_never.
        """
        assert tenacity.stop_never is _make_stop(attempts=None, timeout=None)
