# Changelog

All notable changes to `Ligare.programming`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Review the `Ligare` [CHANGELOG.md](https://github.com/uclahs-cds/Ligare/blob/main/CHANGELOG.md) for full monorepo notes.

---
## Unreleased

## [0.7.1] - 2025-05-23
### Fixed
- Fixed a problem with R serialization when serializing values to character vectors.

## [0.7.0] - 2025-05-12
### Changed
- Changed how R script errors are handled

## [0.6.0] - 2025-04-21
### Added
- Introduced an R integration module `Ligare.programming.R` for executing and communicating with R processes.
- Added types for creating UIs related to R methods.

### Fixed
- Type error uncovered by Pyright update.
- `pytest` warnings caused by unintentionally collecting `TestConfig` as a test class, which is really a stub for testing `AbstractConfig`.

## [0.5.0] - 2025-03-25
### Added
- Introduced generic `ApplicationBuilder` in `Ligare.programming`, usable for CLI and web apps.
- Created support classes for building dynamic configuration with `create_model(...)`.
- Added developer and user documentation via Sphinx.
- Included module docstrings across all `Ligare.programming` components.

### Changed
- Configuration system updated to support optional modules and better typing.
- Builder-related exceptions moved out of `Ligare.web` into `Ligare.programming`.
- Improved logging context and error messages.
- Internal logic updated to gracefully skip AWS modules if not installed.
- Example applications updated to reflect config and builder improvements.

### Fixed
- Fixed warnings from Pydantic config instantiation.
- Addressed multiple Pyright-related type-checking issues.

## [0.4.0] - 2025-01-09
### Added
* Removed `ApplicationBuilder` from Ligare.web and put it in Ligare.programming

## [0.3.0] - 2024-10-04
### Added
* Added `ConfigurableModule` to support automatic inclusion of `Config` classes for Injector `Module`s

### Changed
* Better `ConfigBuilder` support
