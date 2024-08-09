# Changelog

All notable changes to `BL_Python.platform`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Review the `BL_Python` [CHANGELOG.md](https://github.com/uclahs-cds/BL_Python/blob/main/CHANGELOG.md) for full monorepo notes.

---
## Unreleased

## [0.3.0] - 2024-08-09
### Changed
* Abstract feature flag cache and refactor related code so using feature flags is simpler [8b858303](https://github.com/uclahs-cds/BL_Python/commit/8b858303d821354040c099f2bd7f29c23ca4735c)

### Fixed
* Close SQLAlchemy session in Identity user loader when database operations are finished [c5620463](https://github.com/uclahs-cds/BL_Python/commit/c5620463abbd9931993761cc9ad2e9630d4daedd)
* Fix confusion in feature flag caching through refactor and docs update [8b858303](https://github.com/uclahs-cds/BL_Python/commit/8b858303d821354040c099f2bd7f29c23ca4735c)
* Fix interface error in feature flags regarding parameter mismatch and a lie about how database feature flags work [8b858303](https://github.com/uclahs-cds/BL_Python/commit/8b858303d821354040c099f2bd7f29c23ca4735c)

## [0.2.2] - 2024-05-16
### Changed
- Ignore sentinel files created by `make`.

### Fixed
- Resolve implicit join failure in SQLAlchemy when loading user roles during user authorization.
