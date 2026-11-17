# Custom Hooks

If the instrumentation hooks shipped by _stamina_ don't fit your needs, you can easily implement your own, because a hook is just a callable that takes a [`RetryDetails`][stamina.instrumentation.RetryDetails] and does whatever it wants.

For example, this hook prints the details of each scheduled retry:

```python
import stamina


def print_hook(details: stamina.instrumentation.RetryDetails) -> None:
    print("Retry scheduled:", details)


stamina.instrumentation.set_on_retry_hooks([print_hook])
```

Its return value is ignored, unless it's a [context manager](#context-managers).


## Context managers

If you need to know when the backoff ends (for example, to emit a span for the time spent waiting) a hook can also return a context manager.
*stamina* enters it when it schedules the retry and exits it right before the next attempt.
The easiest way is [`contextlib.contextmanager`][]:

```python
import contextlib
import time

from collections.abc import Iterator

import stamina


@contextlib.contextmanager
def print_wait_hook(
    details: stamina.instrumentation.RetryDetails,
) -> Iterator[None]:
    print("Waiting before retry:", details)
    start = time.monotonic()

    yield

    print(f"Retrying now after {time.monotonic() - start:.2f}s.")


stamina.instrumentation.set_on_retry_hooks([print_wait_hook])
```

!!! note
    *stamina* only supports synchronous context managers.


## Hook factories

If your hook needs setup that is expensive, wrap a function that creates the hook in a [`RetryHookFactory`][stamina.instrumentation.RetryHookFactory].
*stamina* calls the factory only once: when it schedules the first retry or an earlier call to [`stamina.instrumentation.get_on_retry_hooks()`][stamina.instrumentation.get_on_retry_hooks].
This is useful, for example, in CLI tools where you want to delay the initialization of the instrumentation until the first retry is scheduled.

```python
import stamina


def make_print_hook() -> stamina.instrumentation.RetryHook:
    print("Initializing the print hook.")

    def print_hook(details: stamina.instrumentation.RetryDetails) -> None:
        print("Retry scheduled:", details)

    return print_hook


stamina.instrumentation.set_on_retry_hooks(
    [stamina.instrumentation.RetryHookFactory(make_print_hook)]
)
```

Now, if you run something like this:

```python
@stamina.retry(on=Exception)
def do_it(arg, kw):
    raise ValueError(arg)


do_it(67, kw=42)
```

You get output like this:

```plain
Initializing the print hook.
Retry scheduled: RetryDetails(name='__main__.do_it', args=(67,), kwargs={'kw': 42}, retry_num=1, wait_for=1.0369990140298804, waited_so_far=0.0, caused_by=ValueError(67))
Retry scheduled: RetryDetails(name='__main__.do_it', args=(67,), kwargs={'kw': 42}, retry_num=2, wait_for=0.2118614697618475, waited_so_far=1.0369990140298804, caused_by=ValueError(67))
...
```
