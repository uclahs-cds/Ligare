import json
import logging
from configparser import ConfigParser
from logging import Logger
from os import environ
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from boto3.session import Session
from Ligare.programming.collections.dict import AnyDict

TConfig = TypeVar("TConfig")


class SSMParameters:
    _log: Logger
    _config: ConfigParser
    _continue_on_ssm_failure: bool = True

    def __init__(self) -> None:
        super().__init__()

        self._log = logging.getLogger("AWS_SSM")

        self._config = ConfigParser()

    def _log_and_conditionally_fail(
        self, msg: str, level: int = logging.INFO, exc_info: Union[bool, int] = 1
    ) -> None:
        """
        If self._continue_on_ssm_failre is True, this function will log.
        If it is False, this function will log and raise an exception.

        msg : str
            The message to log
        level : int
            The log level severity
        exc_info : int, bool
            If True or any non-0 number, exception info will be logged
        """
        if self._continue_on_ssm_failure:
            self._log.log(level, msg, exc_info=bool(exc_info))
        else:
            self._log.log(logging.ERROR, msg, exc_info=bool(exc_info))
            raise Exception(msg)

    def _config_safe_get(self, section: str, option: str) -> str | None:
        return (
            self._config.has_option(section, option)
            and self._config.get(section, option)
            or None
        )

    def load_ssm_application_parameters(
        self, _session: Type[Session] = Session
    ) -> AnyDict | None:
        _ = self._config.read("aws-ssm.ini")

        self._log = logging.getLogger(self._config_safe_get("DEFAULT", "LoggerName"))

        self._continue_on_ssm_failure = (
            self._config_safe_get("DEFAULT", "ContinueOnSSMFailure") == "True"
        )

        USE_SSM_ENVIRONMENT_PARAMETERS = self._config_safe_get(
            "DEFAULT", "UseSSMConfigParameters"
        )
        if not USE_SSM_ENVIRONMENT_PARAMETERS == "True":
            # this will occur if the value is not set at all (is not explicitly "False"),
            # which might not be intentional and so we should conditionally fail.
            if USE_SSM_ENVIRONMENT_PARAMETERS == "False":
                return self._log.info(
                    "UseSSMConfigParameters is 'False'. Skipping SSM parameter lookup."
                )
            else:
                return self._log_and_conditionally_fail(
                    "UseSSMConfigParameters is not set or invalid. Skipping SSM parameter lookup."
                )

        AWS_PROFILE_NAME = self._config_safe_get("AWS", "ProfileName")
        AWS_REGION_NAME = self._config_safe_get("AWS", "RegionName")
        SSM_PARAMETERS_PATH = self._config_safe_get("SSM", "EnvironmentParametersPath")

        if not SSM_PARAMETERS_PATH:
            return self._log_and_conditionally_fail(
                "SSM EnvironmentParametersPath is not defined in aws-ssm.ini. Skipping SSM parameter lookup.",
                logging.WARNING,
            )

        SSM_PARAMETERS_EMPTY_MSG = f"No SSM parameters were found to start the application with. Ensure {SSM_PARAMETERS_PATH} is not empty."

        parameters: Optional[List[Dict[str, str]]]
        try:
            session = _session(
                profile_name=AWS_PROFILE_NAME, region_name=AWS_REGION_NAME
            )
            client: Any = session.client("ssm")  # pyright: ignore[reportUnknownMemberType]
            parameters = client.get_parameters_by_path(
                Path=SSM_PARAMETERS_PATH, WithDecryption=True, MaxResults=1
            ).get("Parameters")
        except Exception as _:
            return self._log_and_conditionally_fail(
                f"Skipping SSM parameter lookup.", logging.WARNING
            )

        if not parameters:
            return self._log_and_conditionally_fail(SSM_PARAMETERS_EMPTY_MSG)

        application_settings_json = parameters[0].get("Value")

        # the application doesn't need to provide any settings
        # through SSM, so do something else instead
        if not application_settings_json:
            return self._log_and_conditionally_fail(SSM_PARAMETERS_EMPTY_MSG)

        application_settings = json.loads(application_settings_json)

        if not application_settings:
            return self._log_and_conditionally_fail(SSM_PARAMETERS_EMPTY_MSG)

        self._log.info(f"SSM application parameters at {SSM_PARAMETERS_PATH} found.")

        return application_settings

    def load_config(self, config_type: type[TConfig]) -> TConfig | None:
        config: TConfig | None = None
        try:
            ssm_parameters = self.load_ssm_application_parameters()

            if ssm_parameters is None:
                raise Exception("SSM parameters were not loaded.")

            config = config_type(**ssm_parameters)
        except:
            if not self._continue_on_ssm_failure:
                raise

        return config

    def update_env(self, application_settings: dict[str, str], log: Logger) -> None:
        try:
            environ.update({
                setting_name: str(value)
                for (setting_name, value) in application_settings.items()
            })
        except Exception as e:
            log.error(
                "Failed to update environment with SSM environment parameters.",
                exc_info=e,
            )
            raise e
