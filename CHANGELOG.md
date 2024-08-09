# Changelog
All notable changes to the BL_Python monorepo and individual packages contained within.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
## Unreleased

# `BL_Python.all` [0.3.0] - 2024-08-09
### Changed
* Update many dependencies
* Abstract feature flag cache and refactor related code so using feature flags is simpler [8b858303](https://github.com/uclahs-cds/BL_Python/commit/8b858303d821354040c099f2bd7f29c23ca4735c)

### Fixed
* Resolve failure in installing correct Pyright version during CICD [c7dddd65](https://github.com/uclahs-cds/BL_Python/commit/c7dddd65b000a3a5f102d52c369a4ee82ccf8e6d)
* Close SQLAlchemy session in Identity user loader when database operations are finished [c5620463](https://github.com/uclahs-cds/BL_Python/commit/c5620463abbd9931993761cc9ad2e9630d4daedd)
* Fix confusion in feature flag caching through refactor and docs update [8b858303](https://github.com/uclahs-cds/BL_Python/commit/8b858303d821354040c099f2bd7f29c23ca4735c)
* Fix interface error in feature flags regarding parameter mismatch and a lie about how database feature flags work [8b858303](https://github.com/uclahs-cds/BL_Python/commit/8b858303d821354040c099f2bd7f29c23ca4735c)
* Resolved several type and style errors arising from Pyright and Ruff updates [6f3675bd](https://github.com/uclahs-cds/BL_Python/commit/6f3675bd5def3d6700da01869f03d39841fc8049)

### Security
* Add dependabot configuration for each BL_Python's Python dependencies [d36e8eda](https://github.com/uclahs-cds/BL_Python/commit/d36e8edaedd5af078be2f0e428790554bc94ab34)


## `BL_Python.AWS` [0.3.0] - 2024-08-09
- [BL_Python.AWS v0.3.0](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.AWS-v0.3.0/src/AWS/CHANGELOG.md#030---2024-08-09)

## `BL_Python.database` [0.2.1] - 2024-08-09
- [BL_Python.database v0.2.1](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.database-v0.2.1/src/database/CHANGELOG.md#021---2024-08-09)

## `BL_Python.platform` [0.3.0] - 2024-08-09
- [BL_Python.platform v0.3.0](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.platform-v0.3.0/src/platform/CHANGELOG.md#030---2024-08-09)

## `BL_Python.web` [0.2.5] - 2024-08-09
- [BL_Python.web v0.2.5](https://github.com/uclahs-cds/BL_Python/blob/BL_Python.web-v0.2.5/src/web/CHANGELOG.md#025---2024-08-09)

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
