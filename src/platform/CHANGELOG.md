# Changelog

All notable changes to `Ligare.platform`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Review the `Ligare` [CHANGELOG.md](https://github.com/uclahs-cds/Ligare/blob/main/CHANGELOG.md) for full monorepo notes.


---
## Unreleased

## [0.8.0] - 2025-03-25
### Added
- Added initial module-level docstrings to `Ligare.platform.__init__` for Sphinx documentation generation.

## [0.7.0] - 2025-01-10
### Fixed
* Changed the base type of FeatureFlag tables to resolve type problems with Pyright

## [0.6.0] - 2025-01-09
### Fixed
* Changed the base type of Identity tables to resolve type problems with Pyright

## [0.5.0] - 2024-11-01
### Added
- Added a function decorator `feature_flag(...)` to control the availability of a function based on a feature flag's enablement. d5d2242
- Added Feature Flag module for querying and altering Feature Flags in a running application.

### Changed
- Alter how FeatureFlags are queried to resolve issues with schemas and multiple `ScopedSession` Injector registrations. 76353a1

## [0.4.0] - 2024-10-04
### Added
* Added a Feature Flag "router" module, supporting both a caching and database backend

### Changed
* Updated Injector modules to be `ConfigurableModule`s instead of Modules

## [0.3.0] - 2024-08-09
### Changed
* Abstract feature flag cache and refactor related code so using feature flags is simpler [8b858303](https://github.com/uclahs-cds/Ligare/commit/8b858303d821354040c099f2bd7f29c23ca4735c)

### Fixed
* Close SQLAlchemy session in Identity user loader when database operations are finished [c5620463](https://github.com/uclahs-cds/Ligare/commit/c5620463abbd9931993761cc9ad2e9630d4daedd)
* Fix confusion in feature flag caching through refactor and docs update [8b858303](https://github.com/uclahs-cds/Ligare/commit/8b858303d821354040c099f2bd7f29c23ca4735c)
* Fix interface error in feature flags regarding parameter mismatch and a lie about how database feature flags work [8b858303](https://github.com/uclahs-cds/Ligare/commit/8b858303d821354040c099f2bd7f29c23ca4735c)

## [0.2.2] - 2024-05-16
### Changed
- Ignore sentinel files created by `make`.

### Fixed
- Resolve implicit join failure in SQLAlchemy when loading user roles during user authorization.
