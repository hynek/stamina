# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from unittest.mock import Mock

import pytest

import stamina


@pytest.mark.parametrize("attempts,timeout", [(None, 1), (1, None)])
async def test_ok(attempts, timeout):
    """
    No error, no problem.
    """

    @stamina.retry(on=Exception, attempts=attempts, timeout=timeout)
    async def f():
        return 42

    assert 42 == await f()


async def test_retries():
    """
    Retries if the specific error is raised.
    """
    i = 0

    @stamina.retry(on=ValueError, wait_max=0)
    async def f():
        nonlocal i
        if i == 0:
            i += 1
            raise ValueError

        return 42

    assert 42 == await f()
    assert 1 == i


async def test_wrong_exception():
    """
    Exceptions that are not passed as `on` are left through.
    """

    @stamina.retry(on=ValueError)
    async def f():
        raise TypeError("passed")

    with pytest.raises(TypeError, match="passed"):
        await f()


async def test_retry_inactive(monkeypatch):
    """
    If inactive, don't retry.
    """

    @stamina.retry(on=Exception)
    async def f():
        raise Exception("passed")

    stamina.set_active(False)

    retrying = Mock()
    monkeypatch.setattr(stamina._sync._t, "Retrying", retrying)

    with pytest.raises(Exception, match="passed"):
        await f()

    retrying.assert_not_called()

