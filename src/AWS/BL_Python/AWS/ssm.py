import json
import logging
from configparser import ConfigParser
from logging import Logger
from os import environ
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from BL_Python.programming.collections.dict import AnyDict
from BL_Python.programming.config import AbstractConfig
from boto3.session import Session
from pydantic import BaseModel


def load_ssm_application_parameters(
    config: ConfigParser, _session: Type[Session] = Session
):
    def config_safe_get(section: str, option: str):
        return (
            config.has_option(section, option) and config.get(section, option) or None
        )

    CONTINUE_ON_SSM_FAILURE = (
        config_safe_get("DEFAULT", "ContinueOnSSMFailure") == "True"
    )

    log = logging.getLogger(config_safe_get("DEFAULT", "LoggerName"))

    def log_and_conditionally_fail(
        msg: str, level: int = logging.INFO, exc_info: Union[bool, int] = 1
    ):
        """
        If CONTINUE_ON_SSM_FAILURE is True, this function will log.
        If it is False, this function will log and raise an exception.

        msg : str
            The message to log
        level : int
            The log level severity
        exc_info : int, bool
            If True or any non-0 number, exception info will be logged
        """
        if CONTINUE_ON_SSM_FAILURE:
            log.log(level, msg, exc_info=bool(exc_info))
        else:
            log.log(logging.ERROR, msg, exc_info=bool(exc_info))
            raise Exception(msg)

    USE_SSM_ENVIRONMENT_PARAMETERS = config_safe_get(
        "DEFAULT", "UseSSMEnvironmentParameters"
    )
    if not USE_SSM_ENVIRONMENT_PARAMETERS == "True":
        # this will occur if the value is not set at all (is not explicitly "False"),
        # which might not be intentional and so we should conditionally fail.
        if USE_SSM_ENVIRONMENT_PARAMETERS == "False":
            return log.info(
                "UseSSMEnvironmentParameters is 'False'. Skipping SSM parameter lookup."
            )
        else:
            return log_and_conditionally_fail(
                "UseSSMEnvironmentParameters is not set or invalid. Skipping SSM parameter lookup."
            )

    AWS_PROFILE_NAME = config_safe_get("AWS", "ProfileName")
    AWS_REGION_NAME = config_safe_get("AWS", "RegionName")
    SSM_PARAMETERS_PATH = config_safe_get("SSM", "EnvironmentParametersPath")

    if not SSM_PARAMETERS_PATH:
        return log_and_conditionally_fail(
            "SSM EnvironmentParametersPath is not defined in aws-ssm.ini. Skipping SSM parameter lookup.",
            logging.WARNING,
        )

    SSM_PARAMETERS_EMPTY_MSG = f"No SSM parameters were found to start the application with. Ensure {SSM_PARAMETERS_PATH} is not empty."

    parameters: Optional[List[Dict[str, str]]]
    try:
        session = _session(profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME)
        client: Any = session.client(
            "ssm",
        )
        parameters = client.get_parameters_by_path(
            Path=SSM_PARAMETERS_PATH, WithDecryption=True, MaxResults=1
        ).get("Parameters")
    except Exception as _:
        return log_and_conditionally_fail(
            f"Skipping SSM parameter lookup.", logging.WARNING
        )

    if not parameters:
        return log_and_conditionally_fail(SSM_PARAMETERS_EMPTY_MSG)

    application_settings_json = parameters[0].get("Value")

    # the application doesn't need to provide any settings
    # through SSM, so do something else instead
    if not application_settings_json:
        return log_and_conditionally_fail(SSM_PARAMETERS_EMPTY_MSG)

    application_settings = json.loads(application_settings_json)

    if not application_settings:
        return log_and_conditionally_fail(SSM_PARAMETERS_EMPTY_MSG)

    log.info(f"SSM application parameters at {SSM_PARAMETERS_PATH} found.")

    return application_settings


def update_env(application_settings: dict[str, str], log: Logger) -> None:
    try:
        environ.update({
            setting_name: str(value)
            for (setting_name, value) in application_settings.items()
        })
    except Exception as e:
        log.error(
            "Failed to update environment with SSM environment parameters.", exc_info=e
        )
        raise e


TConfig = TypeVar("TConfig", bound=BaseModel)


def update_config(
    application_settings: AnyDict, config: type[TConfig], log: Logger
) -> TConfig:
    return config.model_validate(application_settings)
