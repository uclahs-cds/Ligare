# Changelog

All notable changes to `BL_Python.web`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Review the `BL_Python` [CHANGELOG.md](https://github.com/uclahs-cds/BL_Python/blob/main/CHANGELOG.md) for full monorepo notes.

---
## Unreleased

## [0.2.5] - 2024-08-09
### Changed
* Update many dependencies

### Fixed
* Resolved several type and style errors arising from Pyright and Ruff updates [6f3675bd](https://github.com/uclahs-cds/BL_Python/commit/6f3675bd5def3d6700da01869f03d39841fc8049)

## [0.2.4] - 2024-05-30
### Added
- ASGI worker classes to support ASGI lifetime and proxy options when running ASGI applications #68

### Fixed
- Correctly resolve server hostname and remote address when running application with gunicorn #68
- Log correct username #68

## [0.2.3] - 2024-05-17
### Changed
- Flask and OpenAPI apps require configuration of CORS origins as an array
  - Flask apps still only supports a single origin
- OpenAPI apps use `CORSMiddleware` in favor of the custom CORS handlers

### Added
- Custom middleware modules can now use Injector to get interfaces that have been previously registered

## [0.2.2] - 2024-05-16
### Changed
- Ignore sentinel files created by `make`.

### Fixed
- Update type annotation for variable causing new failure in Pyright.
- Resolved crash when query string is stored as a byte array.
