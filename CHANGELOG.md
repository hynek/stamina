# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Calendar Versioning*](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

<!-- changelog follows -->


## [Unreleased](https://github.com/hynek/stamina/compare/22.2.0...HEAD)

### Added

- Official Python 3.12 support.
  [#9](https://github.com/hynek/stamina/pull/9)
- Async support.
  [#10](https://github.com/hynek/stamina/pull/10)
- Retries of arbitrary blocks using (async) `for` loops and context managers.
  [#12](https://github.com/hynek/stamina/pull/12)
- Support to pass `datetime.datetime` objects as *timeout* which is used as a strict deadline.
  [#14](https://github.com/hynek/stamina/pull/14)


### Changed

- The *timeout*, *wait_initial*, *wait_max*, and *wait_jitter* arguments can now also be of type [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta).


## [22.2.0](https://github.com/hynek/stamina/compare/22.1.0...22.2.0) - 2022-10-06

### Added

- Retries are now instrumented.
  If [*prometheus-client*](https://github.com/prometheus/client_python) is installed, retries are counted using the *Prometheus* counter `stamina_retries_total`.
  If [*structlog*](https://www.structlog.org/) is installed, they are logged using a *structlog* logger at warning level.
  These two instrumentations are *independent* from each other.


## [22.1.0](https://github.com/hynek/stamina/tree/22.1.0) - 2022-10-02

### Added

- Initial release.
