import logging
from typing import Any, Tuple

import pytest
from BL_Python.database.config import DatabaseConfig
from BL_Python.database.dependency_injection import ScopedSessionModule
from BL_Python.platform.feature_flag.db_feature_flag_router import (
    DBFeatureFlagRouter,
    FeatureFlagTable,
)
from BL_Python.programming.dependency_injection import ConfigModule
from pytest_mock import MockerFixture
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm.session import Session

_FEATURE_FLAG_TEST_NAME = "foo_feature"
_FEATURE_FLAG_TEST_DESCRIPTION = "foo description"


class PlatformMetaBase(DeclarativeMeta):
    pass


class PlatformBase(object):
    pass


from BL_Python.database.testing.config import inmemory_database_config

PlatformBase = declarative_base(cls=PlatformBase, metaclass=PlatformMetaBase)
FeatureFlag = FeatureFlagTable(PlatformBase)


@pytest.fixture()
def feature_flag_session():
    from injector import Injector

    injector = Injector([
        ConfigModule(inmemory_database_config(), DatabaseConfig),
        ScopedSessionModule(bases=[PlatformBase]),  # pyright: ignore[reportArgumentType]
    ])

    session = injector.get(Session)
    PlatformBase.metadata.create_all(session.bind)  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
    return session


def _create_feature_flag(session: Session):
    session.add(
        FeatureFlag(
            name=_FEATURE_FLAG_TEST_NAME, description=_FEATURE_FLAG_TEST_DESCRIPTION
        )
    )
    session.commit()


def test__feature_is_enabled__defaults_to_false(feature_flag_session: Session):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )
    _create_feature_flag(feature_flag_session)

    # The value is false because it was not explicitly enabled. This is the database default value.
    is_enabled = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == False


def test__feature_is_enabled__defaults_to_false_when_flag_does_not_exist(
    feature_flag_session: Session,
):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )

    is_enabled = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == False


def test__feature_is_enabled__disallows_empty_name(feature_flag_session: Session):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )

    with pytest.raises(ValueError):
        _ = db_feature_flag_router.feature_is_enabled("")


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__feature_is_enabled__disallows_non_string_names(
    name: Any, feature_flag_session: Session
):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )

    with pytest.raises(TypeError):
        _ = db_feature_flag_router.feature_is_enabled(name)


def test__set_feature_is_enabled__fails_when_flag_does_not_exist(
    feature_flag_session: Session,
):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )

    with pytest.raises(LookupError):
        db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, True)


def test__set_feature_is_enabled__disallows_empty_name(feature_flag_session: Session):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )
    _create_feature_flag(feature_flag_session)

    with pytest.raises(ValueError):
        db_feature_flag_router.set_feature_is_enabled("", False)


@pytest.mark.parametrize("name", [0, False, True, {}, [], (0,)])
def test__set_feature_is_enabled__disallows_non_string_names(
    name: Any, feature_flag_session: Session
):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )

    with pytest.raises(TypeError):
        db_feature_flag_router.set_feature_is_enabled(name, False)


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__sets_correct_value(
    enable: bool, feature_flag_session: Session
):
    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(
        FeatureFlag, feature_flag_session, logger
    )
    _create_feature_flag(feature_flag_session)

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    is_enabled = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert is_enabled == enable


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__caches_flags(enable: bool, mocker: MockerFixture):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    session_query_mock = mocker.patch("sqlalchemy.orm.session.Session.query")
    session_mock.query = session_query_mock

    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(FeatureFlag, session_mock, logger)

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert session_query_mock.call_count == 1


@pytest.mark.parametrize("check_cache", [(True, 1), (False, 0)])
def test__feature_is_enabled__checks_cache(
    check_cache: Tuple[bool, int], mocker: MockerFixture
):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    feature_is_enabled_mock = mocker.patch(
        "BL_Python.platform.feature_flag.feature_flag_router.FeatureFlagRouter.feature_is_enabled"
    )
    _ = mocker.patch(
        "BL_Python.platform.feature_flag.feature_flag_router.FeatureFlagRouter.set_feature_is_enabled"
    )

    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(FeatureFlag, session_mock, logger)

    _ = db_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, check_cache[0]
    )

    assert feature_is_enabled_mock.call_count == check_cache[1]


@pytest.mark.parametrize("check_cache", [(True, 0), (False, 1)])
def test__feature_is_enabled__sets_cache(
    check_cache: Tuple[bool, int], mocker: MockerFixture
):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    feature_is_enabled_mock = mocker.patch(
        "BL_Python.platform.feature_flag.feature_flag_router.FeatureFlagRouter.feature_is_enabled"
    )
    set_feature_is_enabled_mock = mocker.patch(
        "BL_Python.platform.feature_flag.feature_flag_router.FeatureFlagRouter.set_feature_is_enabled"
    )
    feature_is_enabled_mock.return_value = True

    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(FeatureFlag, session_mock, logger)

    _ = db_feature_flag_router.feature_is_enabled(
        _FEATURE_FLAG_TEST_NAME, check_cache[0]
    )

    assert set_feature_is_enabled_mock.call_count == check_cache[1]


@pytest.mark.parametrize("enable", [True, False])
def test__set_feature_is_enabled__resets_cache_when_flag_enable_is_set(
    enable: bool, mocker: MockerFixture
):
    session_mock = mocker.patch("sqlalchemy.orm.session.Session")
    session_query_mock = mocker.patch("sqlalchemy.orm.session.Session.query")
    session_mock.query = session_query_mock

    logger = logging.getLogger("FeatureFlagLogger")
    db_feature_flag_router = DBFeatureFlagRouter(FeatureFlag, session_mock, logger)

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, enable)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    first_value = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    db_feature_flag_router.set_feature_is_enabled(_FEATURE_FLAG_TEST_NAME, not enable)
    _ = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)
    second_value = db_feature_flag_router.feature_is_enabled(_FEATURE_FLAG_TEST_NAME)

    assert session_query_mock.call_count == 2
    assert first_value == enable
    assert second_value == (not enable)
