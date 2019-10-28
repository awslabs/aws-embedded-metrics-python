import abc
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.sinks import Sink


class Environment(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def probe() -> bool:
        """Determines whether or not we are executing in this environment"""

    @staticmethod
    @abc.abstractmethod
    def get_name() -> str:
        """Get the environment name. This will be used to set the ServiceName dimension."""

    @staticmethod
    @abc.abstractmethod
    def get_type() -> str:
        """Get the environment type. This will be used to set the ServiceType dimension."""

    @staticmethod
    @abc.abstractmethod
    def get_log_group_name() -> str:
        """Get log group name. This will be used to set the LogGroup dimension."""

    @staticmethod
    @abc.abstractmethod
    def configure_context(context: MetricsContext) -> None:
        """Configure the context with environment properties."""

    @staticmethod
    @abc.abstractmethod
    def get_sink() -> Sink:
        """Create the appropriate sink for this environment."""
