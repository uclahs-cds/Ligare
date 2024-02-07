from logging import Logger
from typing import Protocol, Type, cast

from BL_Python.programming.patterns import Singleton
from injector import inject
from sqlalchemy import Boolean, Column, Unicode
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.session import Session
from typing_extensions import override

from .feature_flag_router import FeatureFlagRouter


class FeatureFlag(Protocol):
    __tablename__: str
    name: Column[Unicode] | str
    enabled: Column[Boolean] | bool
    description: Column[Unicode] | str


class FeatureFlagTable(Singleton):
    def __new__(cls, base: Type[DeclarativeMeta]):
        class FeatureFlag(base):
            """
            A feature flag.
            """

            __tablename__ = "feature_flag"

            name = Column("name", Unicode, primary_key=True, nullable=False)
            enabled = Column("enabled", Boolean, nullable=True, default=False)
            description = Column("description", Unicode, nullable=False)

            @override
            def __repr__(self) -> str:
                return "<FeatureFlag %s>" % (self.name)

        return FeatureFlag


class DBFeatureFlagRouter(FeatureFlagRouter):
    _session: Session

    @inject
    def __init__(self, session: Session, logger: Logger) -> None:
        self._session = session
        super().__init__(logger)

    @override
    def set_feature_is_enabled(self, name: str, is_enabled: bool):
        """
        Enable or disable a feature flag in the database.

        This method caches the value of `is_enabled` for the specified feature flag
        unless saving to the database fails.

        name: The feature flag to check.

        is_enabled: Whether the feature flag is to be enabled or disabled.
        """

        if type(name) != str:
            raise TypeError("`name` must be a string.")

        if not name:
            raise ValueError("`name` parameter is required and cannot be empty.")

        feature_flag: FeatureFlag
        try:
            feature_flag = (
                self._session.query(FeatureFlag)
                .filter(cast(Column[Unicode], FeatureFlag.name) == name)
                .one()
            )
        except NoResultFound as e:
            raise LookupError(
                f"The feature flag `{name}` does not exist. It must be created before being accessed."
            ) from e

        feature_flag.enabled = is_enabled
        self._session.commit()
        super().set_feature_is_enabled(name, is_enabled)

    def feature_is_enabled(self, name: str, check_cache: bool = True) -> bool:  # type: ignore reportIncompatibleMethodOverride
        """
        Determine whether a feature flag is enabled or disabled.
        This method returns False if the feature flag does not exist in the database.

        This method caches the value pulled from the database
        for the specified feature flag. It is only cached if the value is
        pulled from the database. If the flag does not exist, no value is cached.

        name: The feature flag to check.

        check_cache: Whether to use the cached value if it is cached. The default is `True`.
            If the cache is not checked, the new value pulled from the database will be cached.
        """
        if check_cache:
            enabled = super().feature_is_enabled(name, None)
            if enabled is not None:
                return enabled

        feature_flag = (
            self._session.query(FeatureFlag)
            .filter(cast(Column[Unicode], FeatureFlag.name) == name)
            .one_or_none()
        )

        if feature_flag is None:
            self._logger.warn(
                f'Feature flag {name} not found in database. Returning "False" by default.'
            )
            return False

        is_enabled = cast(bool, feature_flag.enabled)

        super().set_feature_is_enabled(name, is_enabled)

        return is_enabled
