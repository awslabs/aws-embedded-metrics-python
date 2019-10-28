import abc
from aws_embedded_metrics.environment import Environment


class EnvironmentProvider(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    async def get() -> Environment:
        """Determine the current runtime environment"""
