# stamina

[![PyPI - Version](https://img.shields.io/pypi/v/stamina.svg)](https://pypi.org/project/stamina)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stamina.svg)](https://pypi.org/project/stamina)
[![License: MIT](https://img.shields.io/badge/license-MIT-C06524)](https://github.com/hynek/stamina/blob/main/LICENSE)


[*tenacity*](https://tenacity.readthedocs.io/) is an *amazing* toolkit for handling retries and I've been using it for years.
However, I've found myself to use only very few knobs and wished it wouldn't erase the types of functions it decorates.

*stamina* is really just a very thin layer around *tenacity* that I've been copy-pasting this code among my projects for a long time:

- Retry on certain exceptions ([`retry_if_exception_type`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.retry.retry_if_exception_type)).
- Wait exponentially with jitter (`wait_exponential_jitter`).
- Limit the number of retries and total time. ([`stop_after_attempt`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.stop.stop_after_attempt) and [`stop_after_delay`](https://tenacity.readthedocs.io/en/latest/api.html#tenacity.stop.stop_after_delay)) (max 10 attempts within 30s by default).
- Preserve type hints.
- Easy deactivation for testing.


## Usage

Currently the API consists on one `stamina.retry()` decorator and three helpers for (de)activating the retrying: `stamina.is_active()`, `stamina.set_active()`,  (it's idempotent: it's no problem to call `set_active(True)` twice in a row).

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


## License

*stamina* is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
