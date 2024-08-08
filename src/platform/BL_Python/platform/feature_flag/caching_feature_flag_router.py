from logging import Logger

from typing_extensions import override

from .feature_flag_router import FeatureFlagRouter


class CachingFeatureFlagRouter(FeatureFlagRouter):
    def __init__(self, logger: Logger) -> None:
        self._logger: Logger = logger
        self._feature_flags: dict[str, bool] = {}
        super().__init__()

    @override
    def _notify_change(
        self, name: str, new_value: bool, old_value: bool | None
    ) -> None:
        if name in self._feature_flags:
            if new_value == old_value:
                self._logger.warn(
                    f"Tried to change feature flag value for '{name}' to the same value. It is already {'enabled' if new_value else 'disabled'}."
                )
            else:
                self._logger.warn(
                    f"Changing feature flag value for '{name}' from `{old_value}` to `{new_value}`."
                )
        else:
            self._logger.warn(f"Setting new feature flag '{name}' to `{new_value}`.")

    def _validate_name(self, name: str):
        if type(name) != str:
            raise TypeError("`name` must be a string.")

        if not name:
            raise ValueError("`name` parameter is required and cannot be empty.")

    @override
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> None:
        """
         Enables or disables a feature flag in the in-memory dictionary of feature flags.

         Subclasses should call this method to validate parameters and cache values.

        :param str name: The feature flag to check.
        :param bool is_enabled: Whether the feature flag is to be enabled or disabled.
        """
        self._validate_name(name)

        if type(is_enabled) != bool:
            raise TypeError("`is_enabled` must be a boolean.")

        self._notify_change(name, is_enabled, self._feature_flags.get(name))

        self._feature_flags[name] = is_enabled

        return super().set_feature_is_enabled(name, is_enabled)

    @override
    def feature_is_enabled(self, name: str, default: bool = False) -> bool:
        """
        Determine whether a feature flag is enabled or disabled.

        Subclasses should call this method to validate parameters and use cached values.

        :param str name: The feature flag to check.
        :param bool default: If the feature flag is not in the in-memory dictionary of flags,
            this is the default value to return. The default parameter value
            when not specified is `False`.
        :return bool: If `True`, the feature is enabled. If `False`, the feature is disabled.
        """
        self._validate_name(name)

        return self._feature_flags.get(name, default)

    def feature_is_cached(self, name: str):
        self._validate_name(name)

        return name in self._feature_flags
