from configparser import ConfigParser
from json import dumps
from unittest.mock import MagicMock

import pytest
from BL_Python.AWS.ssm import SSMParameters
from pytest_mock import MockerFixture


def get_aws_ssm_ini_data(
    use_ssm_config_parameters: bool = True,
    continue_on_ssm_failre: bool = True,
    logger_name: str = "AWS_SSM",
    profile_name: str = "test-aws-role-name",
    region_name: str = "us-west-2",
    environment_parameters_path: str = "/test/ssm/parameters/path",
):
    return f"""[DEFAULT]
    UseSSMConfigParameters = {use_ssm_config_parameters}
    ContinueOnSSMFailure = {continue_on_ssm_failre}
    LoggerName = {logger_name}
    [AWS]
    ProfileName = {profile_name}
    RegionName = {region_name}
    [SSM]
    EnvironmentParametersPath = {environment_parameters_path}
    """


def get_ssm_parameters(dump_json: bool = False):
    data = {
        "FLASK_ENV": "development",
        "DATABASE_CONNECTION_STRING": "sqlite:///:memory:",
        "FLASK_SECRET_KEY": "abc123",
        "LOGLEVEL": "DEBUG",
        "PLAINTEXT_LOG_OUTPUT": 0,
        "SQLALCHEMY_ECHO": 0,
        "PERMANENT_SESSION": 0,
        "PERMANENT_SESSION_LIFETIME": 86400,
        "SERVER_NAME": "localhost:5050",
        "SAML2_METADATA_URL": "https://localhost/sso/saml/metadata",
        "SAML2_RELAY_STATE": "https://localhost:5050",
        "SAML2_METADATA": '<?xml version="1.0" encoding="UTF-8"?>',
    }

    return dumps(data) if dump_json else data


def test__SSMParameters__load_ssm_application_parameters__returns_none_when_config_doesnt_exist(
    mocker: MockerFixture,
):
    _ = mocker.patch(
        "BL_Python.AWS.ssm.ConfigParser",
        # ConfigParser.read returns [] when it can't read any files.
        # This prevents I/O from the test.
        return_value=MagicMock(read=MagicMock(return_value=[])),
    )

    ssm_parameters = SSMParameters()
    parameters = ssm_parameters.load_ssm_application_parameters()

    assert parameters is None


def test__SSMParameters__load_ssm_application_parameters__throws_when_config_data_is_invalid(
    mocker: MockerFixture,
):
    _ = mocker.patch(
        "BL_Python.AWS.ssm.ConfigParser",
        return_value=MagicMock(read=MagicMock(return_value=["/dev/null"])),
    )

    ssm_parameters = SSMParameters()

    # The test forces invalid data, so the method should throw
    with pytest.raises(Exception):
        _ = ssm_parameters.load_ssm_application_parameters()


def test__SSMParameters__load_ssm_application_parameters__uses_configured_profile_name(
    mocker: MockerFixture,
):
    session_mock = mocker.patch("BL_Python.AWS.ssm.Session")
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    ssm_parameters = SSMParameters()
    try:
        _ = ssm_parameters.load_ssm_application_parameters(session_mock)
    except Exception:
        pass

    assert (
        config_parser.get("AWS", "ProfileName")
        == session_mock.call_args.kwargs["profile_name"]
    )


def test__SSMParameters__load_ssm_application_parameters__uses_configured_region(
    mocker: MockerFixture,
):
    session_mock = mocker.patch("BL_Python.AWS.ssm.Session")
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    ssm_parameters = SSMParameters()
    try:
        _ = ssm_parameters.load_ssm_application_parameters(session_mock)
    except Exception:
        pass

    assert (
        config_parser.get("AWS", "RegionName")
        == session_mock.call_args.kwargs["region_name"]
    )


def test__SSMParameters__load_ssm_application_parameters__uses_configured_ssm_path(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    get_parameters_by_path_mock = MagicMock()
    session_mock = mocker.patch(
        "BL_Python.AWS.ssm.Session",
        return_value=MagicMock(
            client=MagicMock(
                return_value=MagicMock(
                    get_parameters_by_path=get_parameters_by_path_mock
                )
            )
        ),
    )

    ssm_parameters = SSMParameters()
    try:
        _ = ssm_parameters.load_ssm_application_parameters(session_mock)
    except Exception:
        pass

    assert (
        config_parser.get("SSM", "EnvironmentParametersPath")
        == get_parameters_by_path_mock.call_args.kwargs["Path"]
    )


def test__SSMParameters__load_ssm_application_parameters__returns_none_when_no_parameters_loaded(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    get_parameters_by_path_mock = MagicMock(
        return_value=MagicMock(get=MagicMock(return_value=None))
    )
    session_mock = mocker.patch(
        "BL_Python.AWS.ssm.Session",
        return_value=MagicMock(
            client=MagicMock(
                return_value=MagicMock(
                    get_parameters_by_path=get_parameters_by_path_mock
                )
            )
        ),
    )

    ssm_parameters = SSMParameters()
    parameters = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert parameters is None


def test__SSMParameters__load_ssm_application_parameters__returns_none_when_no_json_value_loaded(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    get_parameters_by_path_mock = MagicMock(
        return_value=MagicMock(
            get=MagicMock(return_value=[MagicMock(get=MagicMock(return_value=None))])
        )
    )
    session_mock = mocker.patch(
        "BL_Python.AWS.ssm.Session",
        return_value=MagicMock(
            client=MagicMock(
                return_value=MagicMock(
                    get_parameters_by_path=get_parameters_by_path_mock
                )
            )
        ),
    )

    ssm_parameters = SSMParameters()
    parameters = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert parameters is None


def test__SSMParameters__load_ssm_application_parameters__returns_none_when_loaded_json_is_empty(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    get_parameters_by_path_mock = MagicMock(
        return_value=MagicMock(
            get=MagicMock(return_value=[MagicMock(get=MagicMock(return_value=""))])
        )
    )
    session_mock = mocker.patch(
        "BL_Python.AWS.ssm.Session",
        return_value=MagicMock(
            client=MagicMock(
                return_value=MagicMock(
                    get_parameters_by_path=get_parameters_by_path_mock
                )
            )
        ),
    )

    ssm_parameters = SSMParameters()
    parameters = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert parameters is None


def test__SSMParameters__load_ssm_application_parameters__returns_parameters_from_loaded_json(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    get_parameters_by_path_mock = MagicMock(
        return_value=MagicMock(
            get=MagicMock(
                return_value=[
                    MagicMock(get=MagicMock(return_value=get_ssm_parameters(True)))
                ]
            )
        )
    )
    session_mock = mocker.patch(
        "BL_Python.AWS.ssm.Session",
        return_value=MagicMock(
            client=MagicMock(
                return_value=MagicMock(
                    get_parameters_by_path=get_parameters_by_path_mock
                )
            )
        ),
    )

    ssm_parameters = SSMParameters()
    parameters = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert parameters == get_ssm_parameters()
