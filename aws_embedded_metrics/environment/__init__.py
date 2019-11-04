import abc
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.sinks import Sink


class Environment(abc.ABC):
    @abc.abstractmethod
    async def probe(self) -> bool:
        """Determines whether or not we are executing in this environment"""

    @abc.abstractmethod
    def get_name(self) -> str:
        """Get the environment name. This will be used to set the ServiceName dimension."""

    @abc.abstractmethod
    def get_type(self) -> str:
        """Get the environment type. This will be used to set the ServiceType dimension."""

    @abc.abstractmethod
    def get_log_group_name(self) -> str:
        """Get log group name. This will be used to set the LogGroup dimension."""

    @abc.abstractmethod
    def configure_context(self, context: MetricsContext) -> None:
        """Configure the context with environment properties."""

    @abc.abstractmethod
    def get_sink(self) -> Sink:
        """Create the appropriate sink for this environment."""
