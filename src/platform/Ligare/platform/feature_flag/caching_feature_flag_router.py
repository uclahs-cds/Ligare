from logging import Logger
from typing import Generic, Sequence, cast

from injector import inject
from typing_extensions import override

from .feature_flag_router import FeatureFlag as FeatureFlagBaseData
from .feature_flag_router import FeatureFlagChange, FeatureFlagRouter, TFeatureFlag


class FeatureFlag(FeatureFlagBaseData):
    pass


class CachingFeatureFlagRouter(Generic[TFeatureFlag], FeatureFlagRouter[TFeatureFlag]):
    @inject
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
                self._logger.warning(
                    f"Tried to change feature flag value for '{name}' to the same value. It is already {'enabled' if new_value else 'disabled'}."
                )
            else:
                self._logger.warning(
                    f"Changing feature flag value for '{name}' from `{old_value}` to `{new_value}`."
                )
        else:
            self._logger.warning(f"Setting new feature flag '{name}' to `{new_value}`.")

    def _validate_name(self, name: str):
        if type(name) != str:
            raise TypeError("`name` must be a string.")

        if not name:
            raise ValueError("`name` parameter is required and cannot be empty.")

    @override
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> FeatureFlagChange:
        """
         Enables or disables a feature flag in the in-memory dictionary of feature flags.

         Subclasses should call this method to validate parameters and cache values.

        :param str name: The feature flag to check.
        :param bool is_enabled: Whether the feature flag is to be enabled or disabled.
        :return FeatureFlagChange: An object representing the previous and new values of the changed feature flag.
        """
        self._validate_name(name)

        if type(is_enabled) != bool:
            raise TypeError("`is_enabled` must be a boolean.")

        old_enabled_value = self._feature_flags.get(name)
        self._notify_change(name, is_enabled, old_enabled_value)

        self._feature_flags[name] = is_enabled

        _ = super().set_feature_is_enabled(name, is_enabled)

        return FeatureFlagChange(
            name=name, old_value=old_enabled_value, new_value=is_enabled
        )

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

        if type(default) != bool:
            raise TypeError("`default` must be a boolean.")

        return self._feature_flags.get(name, default)

    def feature_is_cached(self, name: str):
        self._validate_name(name)

        return name in self._feature_flags

    @override
    def _create_feature_flag(self, name: str, enabled: bool) -> TFeatureFlag:
        return cast(TFeatureFlag, FeatureFlag(name, enabled))

    @override
    def get_feature_flags(
        self, names: list[str] | None = None
    ) -> Sequence[TFeatureFlag]:
        """
        Get all feature flags and their status.

        :params list[str] | None names: Get only the flags contained in this list.
        :return tuple[TFeatureFlag]: An immutable sequence (a tuple) of feature flags.
        If `names` is `None` this sequence contains _all_ feature flags in the cache. Otherwise, the list is filtered.
        """
        if names is None:
            return tuple(
                self._create_feature_flag(name=key, enabled=value)
                for key, value in self._feature_flags.items()
            )
        else:
            return tuple(
                (
                    self._create_feature_flag(name=key, enabled=value)
                    for key, value in self._feature_flags.items()
                    if key in names
                )
            )
