from aws_embedded_metrics.config.configuration import Configuration
from aws_embedded_metrics.config.environment_configuration_provider import (
    EnvironmentConfigurationProvider,
)

config = EnvironmentConfigurationProvider().get_configuration()


def get_config() -> Configuration:
    """Gets the current configuration"""
    return config
