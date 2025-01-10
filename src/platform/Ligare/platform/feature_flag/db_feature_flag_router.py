from dataclasses import dataclass
from logging import Logger
from typing import Protocol, Sequence, TypeVar, cast, overload

from injector import inject
from sqlalchemy import Boolean, Column, String, Unicode
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.scoping import ScopedSession
from typing_extensions import override

from .caching_feature_flag_router import CachingFeatureFlagRouter
from .feature_flag_router import FeatureFlag as FeatureFlagBaseData
from .feature_flag_router import FeatureFlagChange

TMetaBase = TypeVar("TMetaBase", bound=DeclarativeMeta, covariant=True)


@dataclass(frozen=True)
class FeatureFlag(FeatureFlagBaseData):
    description: str | None


TFeatureFlag = TypeVar("TFeatureFlag", bound=FeatureFlag, covariant=True)


class FeatureFlagTableBase(Protocol[TMetaBase]):
    __tablename__: str

    def __init__(  # pyright: ignore[reportMissingSuperCall]
        self,
        /,
        name: str,
        description: str,
        enabled: bool | None = False,
    ) -> None:
        raise NotImplementedError(
            f"`{FeatureFlagTableBase.__name__}` should only be used for type checking."
        )

    __tablename__: str
    name: str
    description: str
    enabled: bool


class FeatureFlagTable:
    __table_args__ = {"schema": "platform"}

    def __new__(cls, base: TMetaBase) -> type[FeatureFlagTableBase[TMetaBase]]:
        class _FeatureFlag(base):  # pyright: ignore[reportUntypedBaseClass]
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

        return _FeatureFlag


class DBFeatureFlagRouter(CachingFeatureFlagRouter[TFeatureFlag]):
    @inject
    def __init__(
        self,
        feature_flag: type[FeatureFlagTableBase[DeclarativeMeta]],
        scoped_session: ScopedSession,
        logger: Logger,
    ) -> None:
        self._feature_flag = feature_flag
        self._scoped_session = scoped_session
        super().__init__(logger)

    @override
    def set_feature_is_enabled(self, name: str, is_enabled: bool) -> FeatureFlagChange:
        """
        Enable or disable a feature flag in the database.

        This method caches the value of `is_enabled` for the specified feature flag
        unless saving to the database fails.

        :param str name: The feature flag to check.
        :param bool is_enabled: Whether the feature flag is to be enabled or disabled.
        :return FeatureFlagChange: An object representing the previous and new values of the changed feature flag.
        """

        if type(name) != str:
            raise TypeError("`name` must be a string.")

        if not name:
            raise ValueError("`name` parameter is required and cannot be empty.")

        feature_flag: FeatureFlagTableBase[DeclarativeMeta]
        with self._scoped_session() as session:
            try:
                feature_flag = (
                    session.query(self._feature_flag)
                    .filter(self._feature_flag.name == name)
                    .one()
                )
            except NoResultFound as e:
                raise LookupError(
                    f"The feature flag `{name}` does not exist. It must be created before being accessed."
                ) from e

            old_enabled_value = cast(bool | None, feature_flag.enabled)
            feature_flag.enabled = is_enabled
            session.commit()
        _ = super().set_feature_is_enabled(name, is_enabled)

        return FeatureFlagChange(
            name=name, old_value=old_enabled_value, new_value=is_enabled
        )

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

        with self._scoped_session() as session:
            feature_flag = (
                session.query(self._feature_flag)
                .filter(self._feature_flag.name == name)
                .one_or_none()
            )

        if feature_flag is None:
            self._logger.warning(
                f'Feature flag {name} not found in database. Returning "{default}" by default.'
            )
            return default

        is_enabled = cast(bool, feature_flag.enabled)

        _ = super().set_feature_is_enabled(name, is_enabled)

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

        :param list[str] | None names: Get only the flags contained in this list.
        :return tuple[TFeatureFlag]: An immutable sequence (a tuple) of feature flags.
        If `names` is `None` this sequence contains _all_ feature flags in the database. Otherwise, the list is filtered.
        """
        db_feature_flags: list[FeatureFlagTableBase[DeclarativeMeta]]
        with self._scoped_session() as session:
            if names is None:
                db_feature_flags = session.query(self._feature_flag).all()
            else:
                db_feature_flags = (
                    session.query(self._feature_flag)
                    .filter(cast(Column[String], self._feature_flag.name).in_(names))
                    .all()
                )

        feature_flags = tuple(
            self._create_feature_flag(
                name=feature_flag.name,
                enabled=feature_flag.enabled,
                description=feature_flag.description,
            )
            for feature_flag in db_feature_flags
        )

        # cache the feature flags
        for feature_flag in feature_flags:
            _ = super().set_feature_is_enabled(feature_flag.name, feature_flag.enabled)

        return feature_flags
