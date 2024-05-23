from configparser import ConfigParser
from json import dumps
from unittest.mock import MagicMock

import pytest
from BL_Python.AWS.ssm import SSMParameters
from pytest_mock import MockerFixture


def get_aws_ssm_ini_data(
    use_ssm_config_parameters: bool | str | None = True,
    continue_on_ssm_failre: bool | str | None = True,
    logger_name: bool | str | None = "AWS_SSM",
    profile_name: bool | str | None = "test-aws-role-name",
    region_name: bool | str | None = "us-west-2",
    environment_parameters_path: bool | str | None = "/test/ssm/parameters/path",
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


@pytest.mark.parametrize(
    "parameter_value", [None, False, "False", '""', '"False"', '"True"']
)
def test__SSMParameters__load_ssm_application_parameters__skips_loading_ssm_parameters_when_configured_not_to_load(
    parameter_value: bool | str | None,
    mocker: MockerFixture,
):
    session_mock = mocker.patch("BL_Python.AWS.ssm.Session")
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(
        get_aws_ssm_ini_data(use_ssm_config_parameters=parameter_value)
    )
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    ssm_parameters = SSMParameters()
    result = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert result is None


def test__SSMParameters__load_ssm_application_parameters__skips_loading_ssm_parameters_when_no_ssm_path_configured(
    mocker: MockerFixture,
):
    session_mock = mocker.patch("BL_Python.AWS.ssm.Session")
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data(environment_parameters_path=""))
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    ssm_parameters = SSMParameters()
    result = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert result is None


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


def test__SSMParameters__load_ssm_application_parameters__session_instantiation_failure_returns_none(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    def throw():
        raise Exception()

    session_mock = mocker.patch("BL_Python.AWS.ssm.Session", side_effect=throw)

    ssm_parameters = SSMParameters()
    result = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert result is None


def test__SSMParameters__load_ssm_application_parameters__ssm_client_creation_failure_returns_none(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    def throw():
        raise Exception()

    session_mock = mocker.patch(
        "BL_Python.AWS.ssm.Session",
        return_value=MagicMock(client=MagicMock(side_effect=throw)),
    )

    ssm_parameters = SSMParameters()
    result = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert result is None


def test__SSMParameters__load_ssm_application_parameters__ssm_parameter_query_failure_returns_none(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    def throw():
        raise Exception()

    get_parameters_by_path_mock = MagicMock(side_effect=throw)
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
    result = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert result is None


def test__SSMParameters__load_ssm_application_parameters__ssm_parameter_query_get_failure_returns_none(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    def throw():
        raise Exception()

    get_parameters_by_path_mock = MagicMock(
        return_value=MagicMock(get=MagicMock(side_effect=throw))
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
    result = ssm_parameters.load_ssm_application_parameters(session_mock)
    assert result is None


def test__SSMParameters__load_ssm_application_parameters__raises_exception_when_configured_to_raise(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data(continue_on_ssm_failre=False))
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
    with pytest.raises(Exception):
        _ = ssm_parameters.load_ssm_application_parameters(session_mock)


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


def test__SSMParameters__load_ssm_application_parameters__returns_none_when_loaded_json_has_no_settings(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    get_parameters_by_path_mock = MagicMock(
        return_value=MagicMock(
            get=MagicMock(return_value=[MagicMock(get=MagicMock(return_value="{}"))])
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


def test__SSMParameters__load_config__returns_none_when_parameter_load_fails(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data())
    _ = mocker.patch("BL_Python.AWS.ssm.ConfigParser", return_value=config_parser)

    get_parameters_by_path_mock = MagicMock(
        return_value=MagicMock(get=MagicMock(return_value=None))
    )
    _ = mocker.patch(
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
    result = ssm_parameters.load_config(MagicMock())  # pyright: ignore[reportArgumentType]
    assert result is None


def test__SSMParameters__load_config__raises_exception_when_configured_to_raise(
    mocker: MockerFixture,
):
    config_parser = ConfigParser()
    config_parser.read = MagicMock(return_value=["/dev/zero"])
    config_parser.read_string(get_aws_ssm_ini_data(continue_on_ssm_failre=False))
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
    with pytest.raises(Exception):
        _ = ssm_parameters.load_config(MagicMock())  # pyright: ignore[reportArgumentType]


def test__SSMParameters__update_env__updates_envvars_from_provided_parameters(
    mocker: MockerFixture,
):
    update_mock = MagicMock()
    _ = mocker.patch("BL_Python.AWS.ssm.environ", update=update_mock)

    parameters = {"foo": "bar"}
    ssm_parameters = SSMParameters()
    ssm_parameters.update_env(parameters, MagicMock())
    update_mock.assert_any_call(parameters)
