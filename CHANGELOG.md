# Changelog
All notable changes to the BL_Python monorepo and individual packages contained within.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
# `BL_Python.all` [0.2.5] - 2024-05-30

## `BL_Python.web` [0.2.4] - 2024-05-30
- [BL_Python.web v0.2.4](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.web-v0.2.4/src/web/CHANGELOG.md#024---2024-05-30)

# `BL_Python.all` [0.2.4] - 2024-05-17

## `BL_Python.web` [0.2.3] - 2024-05-17
- [BL_Python.web v0.2.3](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.web-v0.2.3/src/web/CHANGELOG.md#023---2024-05-17)

# `BL_Python.all` [0.2.3] - 2024-05-16
- Contains all libraries up to v0.2.1, and `BL_Python.platform` v0.2.2 and `BL_Python.web` v0.2.2

## `BL_Python.web` [0.2.2] - 2024-05-16
- [BL_Python.web v0.2.2](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.web-v0.2.2/src/web/CHANGELOG.md#022---2024-05-16)

## `BL_Python.platform` [0.2.2] - 2024-05-16
- [BL_Python.platform v0.2.2](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.platform-v0.2.2/src/platform/CHANGELOG.md#022---2024-05-16)

# [0.2.0] - 2024-05-14
### Added
- New package `BL_Python.identity` for SSO
- SAML2 support in `BL_Python.web`
- Package interconnectivity for managing user identities in a database and tying into SSO and SAML2
- User session support through `flask-login`
- A Makefile so developers can get started by running `make`
- Many `pytest` fixtures for more easily testing Connexion and Flask applications
- `FlaskContextMiddleware` to make it easier to alter all aspects of an ASGI application in any middleware that runs at any time
- Alembic database migration support in both `BL_Python.database` and scaffolded `BL_Python.web` applications

### Fixed
- Possible crash when using dependency injection in some middlewares
- Inconsistencies in database schema names during application runtime

# [0.1.0] - 2024-02-16
### Added
- Setuptools package configurations for:
  - `BL_Python`
  - `BL_Python.AWS`
  - `BL_Python.database`
  - `BL_Python.development`
  - `BL_Python.platform`
  - `BL_Python.programming`
  - `BL_Python.testing`
  - `BL_Python.testing`
  - `BL_Python.web`
- Flask application scaffolding
- SQLite support
- Various software development tools
- Various utility classes and methods
- PyPI package metadata
- Documentation for usage and development

### Changed
- Updated template files to fit this repo
