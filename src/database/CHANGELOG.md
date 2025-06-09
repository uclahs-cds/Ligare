# Changelog

All notable changes to `Ligare.database`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Review the `Ligare` [CHANGELOG.md](https://github.com/uclahs-cds/Ligare/blob/main/CHANGELOG.md) for full monorepo notes.

---
## Unreleased

## [0.5.1] - 2025-06-09
### Fixed
- Fixed issue with breaking change from Alembic causing migration failures when creating Alembic config.

## [0.5.0] - 2025-03-25
### Added
- Added module-level documentation for all key components in `Ligare.database`, including engines, migrations, and schema.

### Changed
- Alembic no longer runs migrations automatically when `env.py` is imported from outside Alembic CLI.

## [0.4.0] - 2025-01-09
### Fixed
* Changed the base type of Identity tables to resolve type problems with Pyright

## [0.3.1] - 2024-10-11
### Changed
* Cleaned up output of `ligare-alembic`

### Fixed
* Added missing dependency in pyproject.toml

## [0.3.0] - 2024-10-04
### Changed
* Updated Injector modules to be `ConfigurableModule`s instead of Modules

## [0.2.1] - 2024-08-09
### Changed
* Update many dependencies
