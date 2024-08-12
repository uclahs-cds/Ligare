from abc import ABC
from dataclasses import dataclass
from logging import Logger
from typing import Sequence, Type, TypeVar, cast, overload

from injector import inject
from sqlalchemy import Boolean, Column, String, Unicode
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.session import Session
from typing_extensions import override

from .caching_feature_flag_router import CachingFeatureFlagRouter
from .feature_flag_router import FeatureFlag as FeatureFlagBaseData


@dataclass(frozen=True)
class FeatureFlag(FeatureFlagBaseData):
    description: str | None


TFeatureFlag = TypeVar("TFeatureFlag", bound=FeatureFlag, covariant=True)


class FeatureFlagTableBase(ABC):
    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        /,
        name: str,
        description: str,
        enabled: bool | None = False,
    ) -> None:
        raise NotImplementedError(
            f"`{FeatureFlagTableBase.__class__.__name__}` should only be used for type checking."
        )

    __tablename__: str
    name: Column[Unicode] | str
    description: Column[Unicode] | str
    enabled: Column[Boolean] | bool


class FeatureFlagTable:
    def __new__(cls, base: Type[DeclarativeMeta]) -> type[FeatureFlagTableBase]:
        class _FeatureFlag(base):
            """
            A feature flag.
            """

            __tablename__ = "feature_flag"

            name: Column[Unicode] | str = Column(
                "name", Unicode, primary_key=True, nullable=False
            )
            description: Column[Unicode] | str = Column(
                "description", Unicode, nullable=False
            )
            enabled: Column[Boolean] | bool = Column(
                "enabled", Boolean, nullable=True, default=False
            )

            @override
            def __repr__(self) -> str:
                return "<FeatureFlag %s>" % (self.name)

        return cast(type[FeatureFlagTableBase], _FeatureFlag)


class DBFeatureFlagRouter(
    CachingFeatureFlagRouter[TFeatureFlag]
):  # [FeatureFlagData]):
    # The SQLAlchemy table type used for querying from the type[FeatureFlag] database table
    _feature_flag: type[FeatureFlagTableBase]
    # The SQLAlchemy session used for connecting to and querying the database
    _session: Session

    @inject
    def __init__(
        self, feature_flag: type[FeatureFlagTableBase], session: Session, logger: Logger
    ) -> None:
        self._feature_flag = feature_flag
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

        feature_flag: FeatureFlagTableBase
        try:
            feature_flag = (
                self._session.query(self._feature_flag)
                .filter(cast(Column[Unicode], self._feature_flag.name) == name)
                .one()
            )
        except NoResultFound as e:
            raise LookupError(
                f"The feature flag `{name}` does not exist. It must be created before being accessed."
            ) from e

        feature_flag.enabled = is_enabled
        self._session.commit()
        super().set_feature_is_enabled(name, is_enabled)

    @overload
    def feature_is_enabled(self, name: str, default: bool = False) -> bool: ...
    @overload
    def feature_is_enabled(
        self, name: str, default: bool, check_cache: bool = True
    ) -> bool: ...
    @override
    def feature_is_enabled(
        self, name: str, default: bool = False, check_cache: bool = True
    ) -> bool:
        """
        Determine whether a feature flag is enabled or disabled.
        This method returns False if the feature flag does not exist in the database.

        This method caches the value pulled from the database
        for the specified feature flag. It is only cached if the value is
        pulled from the database. If the flag does not exist, no value is cached.

        :param str name: The feature flag to check.
        :param bool default: The default value to return when a flag does not exist.
        :param bool check_cache: Whether to use the cached value if it is cached. The default is `True`.
            If the cache is not checked, the new value pulled from the database will be cached.
        """
        if check_cache and super().feature_is_cached(name):
            return super().feature_is_enabled(name, default)

        feature_flag = (
            self._session.query(self._feature_flag)
            .filter(cast(Column[Unicode], self._feature_flag.name) == name)
            .one_or_none()
        )

        if feature_flag is None:
            self._logger.warning(
                f'Feature flag {name} not found in database. Returning "{default}" by default.'
            )
            return default

        is_enabled = cast(bool, feature_flag.enabled)

        super().set_feature_is_enabled(name, is_enabled)

        return is_enabled

    @override
    def _create_feature_flag(
        self, name: str, enabled: bool, description: str | None = None
    ) -> TFeatureFlag:
        parent_feature_flag = super()._create_feature_flag(name, enabled)
        return cast(
            TFeatureFlag,
            FeatureFlag(
                parent_feature_flag.name, parent_feature_flag.enabled, description
            ),
        )

    @override
    def get_feature_flags(
        self, names: list[str] | None = None
    ) -> Sequence[TFeatureFlag]:
        """
        Get all feature flags and their status from the database.
        This methods updates the cache to the values retrieved from the database.
        names: Get only the flags contained in this list.
        """
        if names is None:
            all_feature_flags = self._session.query(self._feature_flag).all()

            # needed to circumvent list comprehension scope
            # https://docs.python.org/3/reference/datamodel.html#class-object-creation
            _super = super()
            [
                _super.set_feature_is_enabled(
                    cast(str, feature_flag.name), cast(bool, feature_flag.enabled)
                )
                for feature_flag in all_feature_flags
            ]

            return super().get_feature_flags()
        else:
            db_feature_flags = (
                self._session.query(self._feature_flag)
                .filter(cast(Column[String], self._feature_flag.name).in_(names))
                .all()
            )

            feature_flags = tuple(
                self._create_feature_flag(
                    name=cast(str, db_feature_flag.name),
                    enabled=cast(bool, db_feature_flag.enabled),
                    description=cast(str, db_feature_flag.description),
                )
                for db_feature_flag in db_feature_flags
            )

            for feature_flag in feature_flags:
                super().set_feature_is_enabled(feature_flag.name, feature_flag.enabled)

            return feature_flags
