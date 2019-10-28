from aws_embedded_metrics.environment import Environment
from aws_embedded_metrics.environment.environment_provider import EnvironmentProvider
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.config import get_config

Config = get_config()


class MetricsLogger:
    def __init__(
        self, env_provider: EnvironmentProvider, context: MetricsContext = None
    ):
        self.env_provider = env_provider
        self.context: MetricsContext = context or MetricsContext.empty()

    async def flush(self) -> None:
        # resolve the environment and get the sink
        # MOST of the time this will run synchonrously
        # This only runs asynchronously if executing for the
        # first time in a non-lambda environment
        environment = await self.env_provider.get()

        self.__configureContextForEnvironment(environment)
        sink = environment.get_sink()

        # accept and reset the context
        sink.accept(self.context)
        self.context = MetricsContext.empty()

    def __configureContextForEnvironment(self, env: Environment) -> None:
        default_dimensions = {
            # LogGroup name will entirely depend on the environment since there
            # are some cases where the LogGroup cannot be configured (e.g. Lambda)
            "log_group": env.get_log_group_name(),
            "service_name": Config.service_name or env.get_name(),
            "service_type": Config.service_type or env.get_type(),
        }
        self.context.set_default_dimensions(default_dimensions)
        env.configure_context(self.context)
