# Changelog

All notable changes to `Ligare.web`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Review the `Ligare` [CHANGELOG.md](https://github.com/uclahs-cds/Ligare/blob/main/CHANGELOG.md) for full monorepo notes.

---
## Unreleased

## [0.3.2] - 2024-10-11
### Fixed
* Several `ligare-scaffold` bugs. #132

## [0.3.1] - 2024-10-08
### Fixed
* Added `Ligare.AWS` to `Ligare.web` dependencies to fix application start failure

## [0.3.0] - 2024-10-04
### Added
* `Ligare.web.application.ApplicationBuilder` for more robust configuration and instantiation of web applications
* `Ligare.web.middleware.feature_flags.FeatureFlagRouterModule` to support using Feature Flags in web applications
* `Ligare.web.middleware.feature_flags.DBFeatureFlagRouterModule` to support Feature Flags in a database
* `Ligare.web.middleware.feature_flags.CachingFeatureFlagRouterModule` to support an in-memory instance of Feature Flags
* `Ligare.web.middleware.FeatureFlagMiddlewareModule` to support an HTTP API to manage and query Feature Flags

### Changed
* Existing usages of `App[T_app].create` or `create_app` now use `ApplicationBuilder`
* Better static typing support for `Ligare.web.middleware.sso.login_required`
* Updated `Ligare.web.middleware.sso.SAML2MiddlewareModule` to support the config refactor necessary for Feature Flags to function
* Updated Flask/FlaskApp test clients and tests to support refactors in this version
* Reduced unit test run time by avoiding parsing YAML for every test

### Deprecated
* `Ligare.web.application.App[T_app]` and `App[T_app].create`
* `Ligare.web.application.create_app`

### Fixed
* Crash during requests and responses when flask-login has not been configured

## [0.2.5] - 2024-08-09
### Changed
* Update many dependencies

### Fixed
* Resolved several type and style errors arising from Pyright and Ruff updates [6f3675bd](https://github.com/uclahs-cds/Ligare/commit/6f3675bd5def3d6700da01869f03d39841fc8049)

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
