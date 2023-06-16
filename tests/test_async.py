# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT


import pytest

import stamina


@pytest.mark.parametrize("attempts,timeout", [(None, 1), (1, None)])
async def test_ok(attempts, timeout):
    """
    No error, no problem.
    """

    class C:
        @stamina.retry(on=Exception, attempts=attempts, timeout=timeout)
        async def f(self):
            return 42

    @stamina.retry(on=Exception, attempts=attempts, timeout=timeout)
    async def f():
        return 42

    assert 42 == await f()
    assert 42 == await C().f()


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


async def test_retries_method():
    """
    Retries if the specific error is raised.
    """
    i = 0

    class C:
        @stamina.retry(on=ValueError, wait_max=0)
        async def f(self):
            nonlocal i
            if i == 0:
                i += 1
                raise ValueError

            return 42

    assert 42 == await C().f()
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


async def test_retry_inactive():
    """
    If inactive, don't retry.
    """
    num_called = 0

    @stamina.retry(on=Exception)
    async def f():
        nonlocal num_called
        num_called += 1
        raise Exception("passed")

    stamina.set_active(False)

    with pytest.raises(Exception, match="passed"):
        await f()

    assert 1 == num_called


async def test_retry_block():
    """
    Async retry_context blocks are retried.
    """
    num_called = 0

    async for attempt in stamina.retry_context(on=ValueError, wait_max=0):
        with attempt:
            num_called += 1
            if num_called < 2:
                raise ValueError

    assert 2 == num_called


async def test_retry_blocks_can_be_disabled():
    """
    Async context retries respect the config.
    """
    stamina.set_active(False)
    num_called = 0

    with pytest.raises(Exception, match="passed"):
        async for attempt in stamina.retry_context(on=Exception, attempts=2):
            with attempt:
                num_called += 1
                raise Exception("passed")

    assert 1 == num_called
