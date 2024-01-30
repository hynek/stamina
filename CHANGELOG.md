# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Calendar Versioning](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

You can find our backwards-compatibility policy [here](https://github.com/hynek/stamina/blob/main/.github/SECURITY.md).

<!-- changelog follows -->


## [Unreleased](https://github.com/hynek/stamina/compare/24.1.0...HEAD)

### Added

- `stamina.RetryingCaller` and `stamina.AsyncRetryingCaller` that allow even easier retries of single callables: `stamina.RetryingCaller(attempts=5).on(ValueError)(do_something, "foo", bar=42)` and `stamina.RetryingCaller(attempts=5)(ValueError, do_something, "foo", bar=42)` will call `do_something("foo", bar=42)` and retry on `ValueError` up to 5 times.

  `stamina.RetryingCaller` and `stamina.AsyncRetryingCaller` take the same arguments as `stamina.retry()`, except for `on` that can be bound separately.

  [#56](https://github.com/hynek/stamina/pull/56)
  [#57](https://github.com/hynek/stamina/pull/57)


## [24.1.0](https://github.com/hynek/stamina/compare/23.3.0...24.1.0) - 2024-01-03

### Fixed

- *stamina* doesn't retry successful blocks when it's deactivated anymore (yes, you read it right).
  [#54](https://github.com/hynek/stamina/pull/54)


## [23.3.0](https://github.com/hynek/stamina/compare/23.2.0...23.3.0) - 2023-12-05

### Added

- [Trio](https://trio.readthedocs.io/) support!
  [#43](https://github.com/hynek/stamina/pull/43)


## [23.2.0](https://github.com/hynek/stamina/compare/23.1.0...23.2.0) - 2023-10-30

### Added

- Instrumentation is now pluggable!
  You can define your own hooks that are run with retry details whenever a retry is scheduled.
  The documentation now has a [whole chapter on instrumentation](https://stamina.hynek.me/en/stable/instrumentation.html).
  [#37](https://github.com/hynek/stamina/pull/37)

- If *structlog* is not installed, the scheduled retry is now logged using the standard library `logging` module by default.
  [#35](https://github.com/hynek/stamina/pull/35)


### Changed

- Tenacity's internal `AttemptManager` object is no longer exposed to the user.
  This was an oversight and never documented.
  `stamina.retry_context()` now yields instances of `stamina.Attempt`.
  [#22](https://github.com/hynek/stamina/pull/22)

- Initialization of instrumentation is now delayed.
  This means that if there's no retries, there's no startup overhead from importing *structlog* and *prometheus-client*.
  [#34](https://github.com/hynek/stamina/pull/34)

- Some key names in *structlog* log messages have been renamed to better reflect their meaning (`slept` → `waited_so_far`, `attempt` → `retry_num`, and `error` → `caused_by`).
  You can rename them back using *structlog*'s [`structlog.processors.EventRenamer`](https://www.structlog.org/en/stable/api.html#structlog.processors.EventRenamer).
  [#35](https://github.com/hynek/stamina/pull/35)


## [23.1.0](https://github.com/hynek/stamina/compare/22.2.0...23.1.0) - 2023-07-04

### Added

- Official Python 3.12 support.
  [#9](https://github.com/hynek/stamina/pull/9)
- Async support.
  [#10](https://github.com/hynek/stamina/pull/10)
- Retries of arbitrary blocks using (async) `for` loops and context managers.
  [#12](https://github.com/hynek/stamina/pull/12)
- Proper documentation.
  [#16](https://github.com/hynek/stamina/pull/16)
- A backwards-compatibility policy.


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
