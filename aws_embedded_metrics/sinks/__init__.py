import abc
from aws_embedded_metrics.logger.metrics_context import MetricsContext


class Sink(abc.ABC):
    """The mechanism by which logs are sent to their destination."""

    @abc.abstractmethod
    def name(self) -> str:
        """The name of the sink."""

    @abc.abstractmethod
    def accept(self, context: MetricsContext) -> None:
        """Flushes the metrics context to the sink."""
