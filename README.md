# stamina

[![PyPI - Version](https://img.shields.io/pypi/v/stamina.svg)](https://pypi.org/project/stamina)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/stamina.svg)](https://pypi.org/project/stamina)
[![License: MIT](https://img.shields.io/badge/license-MIT-C06524)](https://github.com/hynek/stamina/blob/main/LICENSE)


## Production-grade Retries Made Easy

Transient failures are common in distributed systems.
To make your systems resilient, you need to [**retry** failed operations](https://blog.pragmaticengineer.com/resiliency-in-distributed-systems/#retry).
[Tenacity](https://tenacity.readthedocs.io/) is a *production-ready* and beautifully *composable* toolkit for handling retries.
In practice, only a few knobs are needed (repeatedly!), though.

*stamina* is an **opinionated** thin layer around Tenacity based on best practices to avoid constant copy-pasting and shrink the user error surface:

- Retry only on certain exceptions.
- [Exponential backoff with _jitter_](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) between retries.
- Limit the number of retries **and** total time.
- Automatic **async** support.
- Preserve **type hints** of the decorated callable.
- Count ([Prometheus](https://github.com/prometheus/client_python)) and log ([*structlog*](https://www.structlog.org/)) retries with basic metadata (if they're installed).
- Easy _global_ deactivation for testing.


## Project Information

- [**PyPI**](https://pypi.org/project/stamina/)
- [**Source Code**](https://github.com/hynek/stamina)
- [**Documentation**](https://py-stamina.readthedocs.io/)
- [**Changelog**](https://github.com/hynek/stamina/blob/main/CHANGELOG.md)


## License

*stamina* is written by [Hynek Schlawack](https://hynek.me/) and distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
