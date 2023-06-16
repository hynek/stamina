# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

import datetime as dt

from unittest.mock import Mock

import pytest
import tenacity

import stamina

from stamina._core import _make_stop, _StopBefore


@pytest.mark.parametrize("attempts", [None, 1])
@pytest.mark.parametrize(
    "timeout",
    [None, 1, dt.timedelta(days=1), dt.datetime.now(tz=dt.timezone.utc)],
)
@pytest.mark.parametrize("duration", [1, dt.timedelta(days=1)])
def test_ok(attempts, timeout, duration):
    """
    No error, no problem.
    """

    @stamina.retry(
        on=Exception,
        attempts=attempts,
        timeout=timeout,
        wait_initial=duration,
        wait_max=duration,
        wait_jitter=duration,
    )
    def f():
        return 42

    assert 42 == f()


@pytest.mark.parametrize(
    "timeout",
    [
        None,
        1,
        dt.timedelta(days=1),
        dt.datetime.now(tz=dt.timezone.utc) + dt.timedelta(days=1),
    ],
)
@pytest.mark.parametrize("duration", [0, dt.timedelta(days=0)])
def test_retries(duration, timeout):
    """
    Retries if the specific error is raised.
    """
    i = 0

    @stamina.retry(
        on=ValueError,
        timeout=timeout,
        wait_max=duration,
        wait_initial=duration,
        wait_jitter=duration,
    )
    def f():
        nonlocal i
        if i < 1:
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


def test_retry_inactive():
    """
    If inactive, don't retry.
    """
    num_called = 0

    @stamina.retry(on=Exception)
    def f():
        nonlocal num_called
        num_called += 1
        raise Exception("passed")

    stamina.set_active(False)

    with pytest.raises(Exception, match="passed"):
        f()

    assert 1 == num_called


def test_retry_block():
    """
    Sync retry_context blocks are retried.
    """
    i = 0

    for attempt in stamina.retry_context(on=ValueError, wait_max=0):
        with attempt:
            i += 1
            if i < 2:
                raise ValueError

    assert 2 == i


class TestMakeStop:
    def test_never(self):
        """
        If all conditions are None, return stop_never.
        """
        assert tenacity.stop_never is _make_stop(attempts=None, timeout=None)


class TestStopBefore:
    @pytest.mark.parametrize(
        "deadline, wait_initial, wait_exp_base, wait_jitter",
        [
            (dt.datetime.now(tz=dt.timezone.utc), 1, 1, 1),
            (dt.datetime.now().astimezone(), 1, 1, 1),  # noqa: DTZ005
        ],
    )
    def test_deadline_expired(
        self, deadline, wait_initial, wait_exp_base, wait_jitter
    ):
        """
        If deadline could possibly be overstepped, return True to stop.
        """
        sb = _StopBefore(
            deadline,
            wait_initial=wait_initial,
            wait_exp_base=wait_exp_base,
            wait_jitter=wait_jitter,
        )

        assert sb(Mock(attempt_number=1))
