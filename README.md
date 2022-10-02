# stamina

[![PyPI - Version](https://img.shields.io/pypi/v/stamina.svg)](https://pypi.org/project/stamina)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stamina.svg)](https://pypi.org/project/stamina)
[![License: MIT](https://img.shields.io/badge/license-MIT-C06524)](https://github.com/hynek/stamina/blob/main/LICENSE)


[*Tenacity*](https://tenacity.readthedocs.io/) is an *amazing* and beautifully *composable* toolkit for handling retries that I've been using it for years.
In practice, I've found myself to use only very few knobs and wished it wouldn't erase the types of the callables that I decorate with `@tenacity.retry`.

*stamina* is a very thin layer around *Tenacity* that I've been copy-pasting between my projects for a long time:

- Retry on certain exceptions ([`retry_if_exception_type`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry.retry_if_exception_type)).
- Wait exponentially with jitter (`wait_exponential_jitter`).
- Limit the number of retries and total time. ([`stop_after_attempt`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.stop.stop_after_attempt) and [`stop_after_delay`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.stop.stop_after_delay)).
- Preserve type hints.
- Easy deactivation for testing.

If you need more sophisticated features, you probably should use *Tenacity* directly.
Of course, it's possible that I'll add more features that **I** need.


## Usage

The API consists of a `stamina.retry()` decorator:

```python
import httpx

from stamina import retry

@retry(on=httpx.HTTPError, attempts=3)
def do_it(code: int) -> httpx.Response:
    resp = httpx.get(f"https://httpbin.org/status/{code}")
    resp.raise_for_status()

    return resp

# reveal_type(do_it)
# note: Revealed type is "def (code: builtins.int) -> httpx._models.Response"
```

The decorator takes the following arguments (all time-based arguments are floats of seconds):

**on**: An Exception or a tuple of Exceptions on which the decorated callable will be retried.
There is no default, you _must_ pass this explicitly.

**attempts**: Maximum number of attempts (default: `10`).

**timeout**: Maximum time for all retries.
Can be combined with *attempts* (default: `45`).

**wait_initial**: Minimum first backoff before first retry (default: `0.1`).

**wait_max**: Maximum backoff between retries (default: `5`).

**wait_jitter**: Maximum [_jitter_](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) that is added to retry back-off delays (the actual jitter added is a random number between 0 and *wait_jitter*) (default: `1`).

**wait_exp_base**: The exponential base used to compute the retry backoff (default: `2`).

The backoff for retry attempt number _attempt_ is computed as:

$$\text{backoff}(\text{attempt}) = \text{wait\\_initial} * \text{wait\\_exp\\_base}^{\textbf{attempt} - 1} + \text{random}(0, \text{wait\\_jitter})$$

Since $x^{0}$ is always 1, the first backoff is within $\mathopen{[}\text{wait\\_initial},\text{wait\\_initial} + \text{wait\\_jitter}\mathclose{]}$.
Thus, with default values between 0.1 and 1.1 seconds.

---

If all retries fail, the *last* exception is let through.

---

 There's also two helpers for controlling and inspecting whether retrying is active:
 `stamina.is_active()` and `stamina.set_active()` (it's idempotent: you can call `set_active(True)` as many times as you want in a row).
 This is useful in tests.


## License

*stamina* is written by [Hynek Schlawack](https://hynek.me/) and distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
