# Testing

Testing code that has retry logic can be tricky, therefore *stamina* helps you with dedicated testing helpers.

The easiest way is to disable retries globally using {func}`stamina.set_active`:

```python
import pytest
import stamina

@pytest.fixture(autouse=True, scope="session")
def deactivate_retries():
    stamina.set_active(False)
```

This is a great approach when you're only using the decorator-based API.

---

When you need more control, you're going to use the iterator-based APIs around {func}`stamina.retry_context`.

Here, it can make sense to actually trigger retries and test what happens.
However, you don't want the backoff and you probably don't want to go to the full number of attempts.

For this use-case *stamina* comes with a dedicated testing mode that disables backoff and caps retries -- by default to a single attempt: {func}`stamina.set_testing`.

Therefore this script will only print "trying 1" and "trying 2" very quickly and raise a `ValueError`:

```python
import stamina

stamina.set_testing(True)  # no backoff, 1 attempt
stamina.set_testing(True, attempts=2)  # no backoff, 2 attempts

for attempt in stamina.retry_context(on=ValueError):
    with attempt:
        print("trying", attempt.num)
        raise ValueError("nope")

stamina.set_testing(False)
```
