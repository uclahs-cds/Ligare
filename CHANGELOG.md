# Changelog

All notable changes to the Ligare monorepo and individual packages contained within.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Unreleased

---
## `Ligare.all` [0.10.1] - 2025-05-20

### Added
- `create_BadRequest_response` now accepts a minimal "details" object in Ligare.web.

### `Ligare.web` [0.7.2] - 2025-05-20

* [Ligare.web v0.7.2](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.7.2/src/web/CHANGELOG.md#072---2025-05=20)

---

## `Ligare.all` [0.10.0] - 2025-05-13

### Fixed
- Issue caused by OpenAPI specification resolution in Ligare.web. #222

### `Ligare.programming` [0.7.0] - 2025-05-13

* [Ligare.programming v0.7.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.programming-v0.7.0/src/programming/CHANGELOG.md#070---2025-05-13)

---

## `Ligare.all` [0.9.1] - 2025-04-28

### Fixed
- Issue caused by OpenAPI specification resolution in Ligare.web. #222

### `Ligare.web` [0.7.1] - 2025-04-21

* [Ligare.web v0.7.1](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.7.1/src/web/CHANGELOG.md#071---2025-04-28)

---

## `Ligare.all` [0.9.0] - 2025-04-21

The changes associated with `Ligare.all` `v0.9.0` include new GitHub workflows for publishing releases.

New documentation for R integration is also included, as well as methods for testing Sphinx `doctest`. A cookbook guide has been added to work with the `pythonipc` Python and R libraries.

### Added
- Introduced an R integration module `Ligare.programming.R` for executing and communicating with R processes.
- Added types for creating UIs related to R methods.
- Flask Response utility methods for BadRequest and image downloads.

### Fixed
- Type error uncovered by Pyright update.
- `pytest` warnings caused by unintentionally collecting `TestConfig` as a test class, which is really a stub for testing `AbstractConfig`.

### `Ligare.AWS` [0.4.1] - 2025-04-21

* [Ligare.AWS v0.4.1](https://github.com/uclahs-cds/Ligare/blob/Ligare.AWS-v0.4.1/src/AWS/CHANGELOG.md#041---2025-04-21)

### `Ligare.platform` [0.8.1] - 2025-04-21

* [Ligare.platform v0.8.1](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.8.1/src/platform/CHANGELOG.md#081---2025-04-21)

### `Ligare.programming` [0.6.0] - 2025-04-21

* [Ligare.programming v0.6.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.programming-v0.6.0/src/programming/CHANGELOG.md#060---2025-04-21)

### `Ligare.web` [0.7.0] - 2025-04-21

* [Ligare.web v0.7.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.7.0/src/web/CHANGELOG.md#070---2025-04-21)

---

## `Ligare.all` [0.8.0] - 2025-03-25

`Ligare.all` `v0.8.0` introduces a unified `ApplicationBuilder` for both web and CLI apps, significantly simplifying how applications are constructed, configured, and documented. This release also brings first-class Sphinx documentation, improved logging, and broader static typing support - making Ligare easier to understand, extend, and debug across all environments.

### Added

* Add Sphinx. This includes configurations for Sphinx and generating Ligare documentation. It also includes a handful of docstring fixes to make Sphinx happy.
* Add a run method to `CreateAppResult` to make everyone's lives easier.
* Add additional documentation.
* Add `ApplicationBuilder` class to `Ligare.programming`. This class is partly a copy of the builder in `Ligare.web`, but more generic. This is a precursor to further refactoring and switching `Ligare.web` to use the `programming` builder.
* Add module-level docstrings to many libraries to support Sphinx documentation:
  * Ligare.AWS
  * Ligare.GitHub
  * Ligare.database
  * Ligare.identity
  * Ligare.platform
  * Ligare.testing
  * Ligare.web

### Changed

* Rework how configuration is executed and structured.
* Refactor application construction: `ApplicationBuilder` now moved to `Ligare.programming` and is used in both CLI and web apps.
* Configuration values are now accessible prior to app startup, enabling more flexible injector module logic.
* Swagger UI no longer crashes when the Swagger URL is set to `/`.
* Brought scaffolder templates in line with the latest `Ligare` platform updates.
* Flask environment variables are now normalized to lowercase in config.
* Prevent Alembic migrations from executing if `env.py` is imported outside of Alembic CLI.
* Updated how `import_name` is handled; apps can now rely on config rather than hardcoded names.
* Internal typing updated with `create_model(...)` instead of `type(...)` to support dynamic Pydantic config types.
* Logging now uses structured JSON context internally, removing reliance on third-party libraries.
* Improved error messaging and CLI-friendly behavior for `ApplicationBuilder`.

### Fixed

* Fixed Swagger route collision when base path is `/`.
* Corrected in-memory DB not being used in web app tests.
* Protected logger formats from being overwritten during init.
* Numerous type errors, warnings, and compatibility issues resolved with Pyright and Pydantic.
* Restored behavior of test scaffolding logic that previously broke with new module ordering.

### Removed

* Removed deprecated `create_app` and `App[T].create_app` in favor of `ApplicationBuilder`.
* Removed `json_logging`, which is no longer maintained and incompatible with Connexion ≥ 3.x.

### `Ligare.AWS` [0.4.0] - 2025-03-25

* [Ligare.AWS v0.4.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.AWS-v0.4.0/src/AWS/CHANGELOG.md#040---2025-03-25)

### `Ligare.GitHub` [0.3.0] - 2025-03-25

* [Ligare.GitHub v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.GitHub-v0.3.0/src/GitHub/CHANGELOG.md#030---2025-03-25)

### `Ligare.database` [0.5.0] - 2025-03-25

* [Ligare.database v0.5.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.database-v0.5.0/src/database/CHANGELOG.md#050---2025-03-25)

### `Ligare.development` [0.3.0] - 2025-03-25

* [Ligare.development v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.development-v0.3.0/src/development/CHANGELOG.md#030---2025-03-25)

### `Ligare.identity` [0.4.0] - 2025-03-25

* [Ligare.identity v0.4.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.identity-v0.4.0/src/identity/CHANGELOG.md#040---2025-03-25)

### `Ligare.platform` [0.8.0] - 2025-03-25

* [Ligare.platform v0.8.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.8.0/src/platform/CHANGELOG.md#080---2025-03-25)

### `Ligare.programming` [0.5.0] - 2025-03-25

* [Ligare.programming v0.5.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.programming-v0.5.0/src/programming/CHANGELOG.md#050---2025-03-25)

### `Ligare.testing` [0.3.0] - 2025-03-25

* [Ligare.testing v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.testing-v0.3.0/src/testing/CHANGELOG.md#030---2025-03-25)

### `Ligare.web` [0.6.0] - 2025-03-25

* [Ligare.web v0.6.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.6.0/src/web/CHANGELOG.md#060---2025-03-25)

---

## `Ligare.all` [0.7.0] - 2025-01-10

## Changed

* Updated Feature Flag middleware in Ligare.web to resolve new Pyright issues

## Fixed

* Changed the base type of FeatureFlag tables to resolve type problems with Pyright

### `Ligare.platform` [0.7.0] - 2025-01-10

* [Ligare.platform v0.7.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.7.0/src/platform/CHANGELOG.md#070---2025-01-10)

### `Ligare.web` [0.5.1] - 2025-01-10

* [Ligare.web v0.5.1](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.5.1/src/web/CHANGELOG.md#051---2025-01-10)

---

## `Ligare.all` [0.6.0] - 2025-01-09

### Changed

* Updated to Flask 3.1.0 and Connexion 3.2.0
* Removed `ApplicationBuilder` from Ligare.web and put it in Ligare.programming
* Altered several aspects of application construction, configuration, and usage

### Fixed

* Fixed problems with Scaffolded applications behaving differently with test and database modules depending on their specified order on the command-line #151
* Changed the base type of Identity tables to resolve type problems with Pyright

### Deprecated

* Removed previously deprecated `create_app` and `App[T].create_app` functions

### `Ligare.database` [0.4.0] - 2025-01-09

* [Ligare.database v0.4.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.database-v0.4.0/src/database/CHANGELOG.md#040---2025-01-09)

### `Ligare.platform` [0.6.0] - 2025-01-09

* [Ligare.platform v0.6.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.6.0/src/platform/CHANGELOG.md#060---2025-01-09)

### `Ligare.programming` [0.4.0] - 2025-01-09

* [Ligare.programming v0.4.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.programming-v0.4.0/src/programming/CHANGELOG.md#040---2025-01-09)

### `Ligare.web` [0.5.0] - 2025-01-09

* [Ligare.web v0.5.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.5.0/src/web/CHANGELOG.md#050---2025-01-09)

---

## `Ligare.all` [0.5.0] - 2024-11-01

### Added

* Added a function decorator `feature_flag(...)` to control the availability of a function based on a feature flag's enablement. d5d2242
* Added Feature Flag module for querying and altering Feature Flags in a running application.
* Added Feature Flag API for managing Feature Flags in a running web application.
* Added a Makefile to the files generated by the web application scaffolder. bd3d685
* Added optional "VSCode" modules to web application scaffolder to make debugging scaffolded web applications easier. e4646ec

### Changed

* Alter how FeatureFlags are queried to resolve issues with schemas and multiple `ScopedSession` Injector registrations. 76353a1
* Use hostname and port from configuration file to avoid confusion about how to actually access a running web application. 3426b8f

### Fixed

* Fix failures from some automated tests for web application scaffolder. 6a2ce8b
* Fix several static type errors.

### `Ligare.platform` [0.5.0] - 2024-11-01

* [Ligare.platform v0.5.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.5.0/src/platform/CHANGELOG.md#050---2024-11-01)

### `Ligare.web` [0.4.0] - 2024-11-01

* [Ligare.web v0.4.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.4.0/src/web/CHANGELOG.md#040---2024-11-01)

---

## `Ligare.all` [0.4.1] - 2024-10-11

### Fixed

* Several `ligare-scaffold` bugs. #132
* Cleaned up output of `ligare-alembic`

### `Ligare.web` [0.3.2] - 2024-10-11

* [Ligare.web v0.3.2](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.3.2/src/web/CHANGELOG.md#032---2024-10-11)

### `Ligare.database` [0.3.1] - 2024-10-11

* [Ligare.database v0.3.1](https://github.com/uclahs-cds/Ligare/blob/Ligare.database-v0.3.1/src/database/CHANGELOG.md#031---2024-10-11)

---

## `Ligare.all` [0.4.1] - 2024-10-08

### Fixed

* Added `Ligare.AWS` to `Ligare.web` dependencies to fix application start failure

### `Ligare.web` [0.3.1] - 2024-10-08

* [Ligare.web v0.3.1](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.3.1/src/web/CHANGELOG.md#031---2024-10-08)

---

## `Ligare.all` [0.4.0] - 2024-10-04

### Added

* Feature Flags Injector module and API <https://github.com/uclahs-cds/Ligare/pull/107/>

### `Ligare.database` [0.3.0] - 2024-10-04

* [Ligare.database v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.database-v0.3.0/src/database/CHANGELOG.md#030---2024-10-04)

### `Ligare.identity` [0.3.0] - 2024-10-04

* [Ligare.identity v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.identity-v0.3.0/src/identity/CHANGELOG.md#030---2024-10-04)

### `Ligare.platform` [0.4.0] - 2024-10-04

* [Ligare.platform v0.4.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.4.0/src/platform/CHANGELOG.md#040---2024-10-04)

### `Ligare.programming` [0.3.0] - 2024-10-04

* [Ligare.programming v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.programming-v0.3.0/src/programming/CHANGELOG.md#030---2024-10-04)

### `Ligare.web` [0.3.0] - 2024-10-04

* [Ligare.web v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.3.0/src/web/CHANGELOG.md#030---2024-10-04)

---

## `Ligare.all` [0.3.0] - 2024-08-09

### Changed

* Update many dependencies
* Abstract feature flag cache and refactor related code so using feature flags is simpler [8b858303](https://github.com/uclahs-cds/Ligare/commit/8b858303d821354040c099f2bd7f29c23ca4735c)

### Fixed

* Resolve failure in installing correct Pyright version during CICD [c7dddd65](https://github.com/uclahs-cds/Ligare/commit/c7dddd65b000a3a5f102d52c369a4ee82ccf8e6d)
* Close SQLAlchemy session in Identity user loader when database operations are finished [c5620463](https://github.com/uclahs-cds/Ligare/commit/c5620463abbd9931993761cc9ad2e9630d4daedd)
* Fix confusion in feature flag caching through refactor and docs update [8b858303](https://github.com/uclahs-cds/Ligare/commit/8b858303d821354040c099f2bd7f29c23ca4735c)
* Fix interface error in feature flags regarding parameter mismatch and a lie about how database feature flags work [8b858303](https://github.com/uclahs-cds/Ligare/commit/8b858303d821354040c099f2bd7f29c23ca4735c)
* Resolved several type and style errors arising from Pyright and Ruff updates [6f3675bd](https://github.com/uclahs-cds/Ligare/commit/6f3675bd5def3d6700da01869f03d39841fc8049)

### Security

* Add dependabot configuration for each Ligare's Python dependencies [d36e8eda](https://github.com/uclahs-cds/Ligare/commit/d36e8edaedd5af078be2f0e428790554bc94ab34)

### `Ligare.AWS` [0.3.0] - 2024-08-09

* [Ligare.AWS v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.AWS-v0.3.0/src/AWS/CHANGELOG.md#030---2024-08-09)

### `Ligare.database` [0.2.1] - 2024-08-09

* [Ligare.database v0.2.1](https://github.com/uclahs-cds/Ligare/blob/Ligare.database-v0.2.1/src/database/CHANGELOG.md#021---2024-08-09)

### `Ligare.platform` [0.3.0] - 2024-08-09

* [Ligare.platform v0.3.0](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.3.0/src/platform/CHANGELOG.md#030---2024-08-09)

### `Ligare.web` [0.2.5] - 2024-08-09

* [Ligare.web v0.2.5](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.2.5/src/web/CHANGELOG.md#025---2024-08-09)

## `Ligare.all` [0.2.5] - 2024-05-30

### `Ligare.web` [0.2.4] - 2024-05-30

* [Ligare.web v0.2.4](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.2.4/src/web/CHANGELOG.md#024---2024-05-30)

## `Ligare.all` [0.2.4] - 2024-05-17

### `Ligare.web` [0.2.3] - 2024-05-17

* [Ligare.web v0.2.3](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.2.3/src/web/CHANGELOG.md#023---2024-05-17)

## `Ligare.all` [0.2.3] - 2024-05-16

* Contains all libraries up to v0.2.1, and `Ligare.platform` v0.2.2 and `Ligare.web` v0.2.2

### `Ligare.web` [0.2.2] - 2024-05-16

* [Ligare.web v0.2.2](https://github.com/uclahs-cds/Ligare/blob/Ligare.web-v0.2.2/src/web/CHANGELOG.md#022---2024-05-16)

### `Ligare.platform` [0.2.2] - 2024-05-16

* [Ligare.platform v0.2.2](https://github.com/uclahs-cds/Ligare/blob/Ligare.platform-v0.2.2/src/platform/CHANGELOG.md#022---2024-05-16)

## [0.2.0] - 2024-05-14

### Added

* New package `Ligare.identity` for SSO
* SAML2 support in `Ligare.web`
* Package interconnectivity for managing user identities in a database and tying into SSO and SAML2
* User session support through `flask-login`
* A Makefile so developers can get started by running `make`
* Many `pytest` fixtures for more easily testing Connexion and Flask applications
* `FlaskContextMiddleware` to make it easier to alter all aspects of an ASGI application in any middleware that runs at any time
* Alembic database migration support in both `Ligare.database` and scaffolded `Ligare.web` applications

### Fixed

* Possible crash when using dependency injection in some middlewares
* Inconsistencies in database schema names during application runtime

## [0.1.0] - 2024-02-16

### Added

* Setuptools package configurations for:
  * `Ligare`
  * `Ligare.AWS`
  * `Ligare.database`
  * `Ligare.development`
  * `Ligare.platform`
  * `Ligare.programming`
  * `Ligare.testing`
  * `Ligare.testing`
  * `Ligare.web`
* Flask application scaffolding
* SQLite support
* Various software development tools
* Various utility classes and methods
* PyPI package metadata
* Documentation for usage and development

### Changed

* Updated template files to fit this repo
