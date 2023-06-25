# stamina

[![Documentation at ReadTheDocs](https://img.shields.io/badge/Docs-Read%20The%20Docs-black)](https://stamina.hynek.me)
[![PyPI - Version](https://img.shields.io/pypi/v/stamina.svg)](https://pypi.org/project/stamina)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stamina.svg)](https://pypi.org/project/stamina)
[![License: MIT](https://img.shields.io/badge/license-MIT-C06524)](https://github.com/hynek/stamina/blob/main/LICENSE)


## Production-grade Retries Made Easy

Transient failures are common in distributed systems.
To make your systems resilient, you need to **retry** failed operations.
But bad retries can make things *much worse*.

*stamina* is an opinionated wrapper around the *great-but-unopinionated* [Tenacity](https://tenacity.readthedocs.io/) package.
Its goal is to make it easy to do the right thing with *good defaults* based on best practices and shrinking the user error surface.
It is the result of years of copy-pasting the same configuration over and over again:

- Retry only on certain exceptions.
- Exponential backoff with _jitter_ between retries.
- Limit the number of retries **and** total time.
- Automatic **async** support.
- Preserve **type hints** of the decorated callable.
- Count ([Prometheus](https://github.com/prometheus/client_python)) and log ([*structlog*](https://www.structlog.org/)) retries with basic metadata, if they're installed.
- Easy _global_ deactivation for testing.

For example:

```python
import httpx

import stamina


@stamina.retry(on=httpx.HTTPError, attempts=3)
def do_it(code: int) -> httpx.Response:
    resp = httpx.get(f"https://httpbin.org/status/{code}")
    resp.raise_for_status()

    return resp
```

**Async** callables work use the same API and it's possible to retry **arbitrary blocks**, too.
Please refer to our [tutorial](https://stamina.hynek.me/en/latest/tutorial.html) for more examples.


## Project Information

- [**PyPI**](https://pypi.org/project/stamina/)
- [**Source Code**](https://github.com/hynek/stamina)
- [**Documentation**](https://stamina.hynek.me)
- [**Changelog**](https://github.com/hynek/stamina/blob/main/CHANGELOG.md)


## License

*stamina* is written by [Hynek Schlawack](https://hynek.me/) and distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
