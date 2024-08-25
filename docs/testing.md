# Testing

Testing code with retry logic can be tricky, so *stamina* provides dedicated testing helpers that allow you to affect retrying behavior *globally*.


## Turn Off Retries

The easiest way is to turn off retries using {func}`stamina.set_active`:

```python
import pytest
import stamina

@pytest.fixture(autouse=True, scope="session")
def deactivate_retries():
    stamina.set_active(False)
```

This is a great approach when you're only using our decorator-based API.


## Limiting Retries

:::{versionadded} 24.3.0
:::

When you need more control, you can use the iterator-based APIs around {func}`stamina.retry_context`.

In that case, triggering retries and testing what happens can make sense.
However, you don't want the backoff and probably want to avoid going to the full number of attempts -- otherwise, your test suite will run forever.

For this use-case, *stamina* comes with a dedicated testing mode that turns off backoff and caps retries -- by default to a single attempt: {func}`stamina.set_testing`.

Therefore, this script will only print "trying 1" and "trying 2" very quickly and raise a `ValueError`:

```python
import stamina

stamina.set_testing(True)  # no backoff, 1 attempt
stamina.set_testing(True, attempts=2)  # no backoff, 2 attempts

for attempt in stamina.retry_context(on=ValueError, attempts=1_000):
    with attempt:
        print("trying", attempt.num)
        raise ValueError("nope")

stamina.set_testing(False)  # back to business as usual
```
