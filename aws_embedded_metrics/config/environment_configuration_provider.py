import os
from aws_embedded_metrics.config.configuration import Configuration

ENV_VAR_PREFIX = "AWS_EMF"

ENABLE_DEBUG_LOGGING = "ENABLE_DEBUG_LOGGING"
SERVICE_NAME = "SERVICE_NAME"
SERVICE_TYPE = "SERVICE_TYPE"
LOG_GROUP_NAME = "LOG_GROUP_NAME"
LOG_STREAM_NAME = "LOG_STREAM_NAME"
AGENT_ENDPOINT = "AGENT_ENDPOINT"
EC2_METADATA_ENDPOINT = "EC2_METADATA_ENDPOINT"


class EnvironmentConfigurationProvider:
    """
    Loads configuration from environment variables
    """

    def get_configuration(self) -> Configuration:
        return Configuration(
            self.__get_bool_env_var(ENABLE_DEBUG_LOGGING),
            self.__get_env_var(SERVICE_NAME),
            self.__get_env_var(SERVICE_TYPE),
            self.__get_env_var(LOG_GROUP_NAME),
            self.__get_env_var(LOG_STREAM_NAME),
            self.__get_env_var(AGENT_ENDPOINT),
            self.__get_env_var(EC2_METADATA_ENDPOINT),
        )

    @staticmethod
    def __get_env_var(key: str) -> str:
        value = os.environ.get(f"{ENV_VAR_PREFIX}_{key}")
        if value is None:
            return ""
        return value

    @staticmethod
    def __get_bool_env_var(key: str) -> bool:
        value = os.environ.get(f"{ENV_VAR_PREFIX}_{key}")
        if value is None:
            return False
        return value.lower() == "true"
