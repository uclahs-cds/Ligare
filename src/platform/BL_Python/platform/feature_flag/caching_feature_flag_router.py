from logging import Logger

from typing_extensions import override

from .feature_flag_router import FeatureFlagRouter


class CachingFeatureFlagRouter(FeatureFlagRouter):
    def __init__(self, logger: Logger) -> None:
        self._logger: Logger = logger
        self._feature_flags: dict[str, bool] = {}
        super().__init__()

    def _notify_changed(self, name: str):
        if name in self._feature_flags:
            self._logger.warn(
                f"Overridding feature flag value for '{name}'. Toggling from {self._feature_flags[name]} to {self._feature_flags[name]}"
            )

    @override
    def _notify_enabled(self, name: str):
        self._notify_changed(name)
        super()._notify_enabled(name)

    @override
    def _notify_disabled(self, name: str):
        self._notify_changed(name)
        super()._notify_disabled(name)

    @override
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> None:
        """
        Enables or disables a feature flag in the in-memory dictionary of feature flags.

        Subclasses should call this method to validate parameters and cache values.

        name: The feature flag to check.

        is_enabled: Whether the feature flag is to be enabled or disabled.
        """
        if type(name) != str:
            raise TypeError("`name` must be a string.")

        if type(is_enabled) != bool:
            raise TypeError("`is_enabled` must be a boolean.")

        if not name:
            raise ValueError("`name` parameter is required and cannot be empty.")

        self._notify_changed(name)

        self._feature_flags[name] = is_enabled

        return super().set_feature_is_enabled(name, is_enabled)

    @override
    def feature_is_enabled(
        self, name: str, default: bool | None = False
    ) -> bool | None:
        """
        Determine whether a feature flag is enabled or disabled.

        Subclasses should call this method to validate parameters and use cached values.

        name: The feature flag to check.

        default: If the feature flag is not in the in-memory dictionary of flags,
            this is the default value to return. The default parameter value
            when not specified is `False`.
        """
        if type(name) != str:
            raise TypeError("`name` must be a string.")

        if not name:
            raise ValueError("`name` parameter is required and cannot be empty.")

        if name in self._feature_flags:
            return self._feature_flags[name]

        return default
