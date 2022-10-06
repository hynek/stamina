# Changelog

All notable changes to this project will be documented in this file.

The format is based on [*Keep a Changelog*](https://keepachangelog.com/en/1.0.0/) and this project adheres to [*Calendar Versioning*](https://calver.org/).

The **first number** of the version is the year.
The **second number** is incremented with each release, starting at 1 for each year.
The **third number** is for emergencies when we need to start branches for older releases.

<!-- changelog follows -->


## [22.2.0](https://github.com/hynek/stamina/compare/22.1.0...22.2.0) - 2022-10-06

### Added

- Retries are now instrumented.
  If [*prometheus-client*](https://github.com/prometheus/client_python) is installed, retries are counted using the *Prometheus* counter `stamina_retries_total`.
  If [*structlog*](https://www.structlog.org/) is installed, they are logged using a *structlog* logger at warning level.
  These two instrumentations are *independent* from each other.


## [22.1.0](https://github.com/hynek/stamina/tree/22.1.0) - 2022-10-02

### Added

- Initial release.
