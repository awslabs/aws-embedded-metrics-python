# Copyright 2019 Amazon.com, Inc. or its affiliates.
# Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from aws_embedded_metrics.environment import Environment
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.config import get_config
from typing import Any, Awaitable, Callable, Dict, Tuple
import sys
import traceback

Config = get_config()


class MetricsLogger:
    def __init__(
        self,
        resolve_environment: Callable[..., Awaitable[Environment]],
        context: MetricsContext = None,
    ):
        self.resolve_environment = resolve_environment
        self.context: MetricsContext = context or MetricsContext.empty()

    async def flush(self) -> None:
        # resolve the environment and get the sink
        # MOST of the time this will run synchonrously
        # This only runs asynchronously if executing for the
        # first time in a non-lambda environment
        environment = await self.resolve_environment()

        self.__configureContextForEnvironment(environment)
        sink = environment.get_sink()

        # accept and reset the context
        sink.accept(self.context)
        self.context = self.context.create_copy_with_context()

    def __configureContextForEnvironment(self, env: Environment) -> None:
        default_dimensions = {
            # LogGroup name will entirely depend on the environment since there
            # are some cases where the LogGroup cannot be configured (e.g. Lambda)
            "LogGroup": env.get_log_group_name(),
            "ServiceName": Config.service_name or env.get_name(),
            "ServiceType": Config.service_type or env.get_type(),
        }
        self.context.set_default_dimensions(default_dimensions)
        env.configure_context(self.context)

    def set_property(self, key: str, value: Any) -> "MetricsLogger":
        self.context.set_property(key, value)
        return self

    def put_dimensions(self, dimensions: Dict[str, str]) -> "MetricsLogger":
        self.context.put_dimensions(dimensions)
        return self

    def set_dimensions(self, *dimensions: Dict[str, str]) -> "MetricsLogger":
        self.context.set_dimensions(list(dimensions))
        return self

    def set_namespace(self, namespace: str) -> "MetricsLogger":
        self.context.namespace = namespace
        return self

    def put_metric(self, key: str, value: float, unit: str = "None") -> "MetricsLogger":
        self.context.put_metric(key, value, unit)
        return self

    def add_stack_trace(self, key: str, details: Any = None, exc_info: Tuple = None) -> "MetricsLogger":
        if not exc_info:
            exc_info = sys.exc_info()

        err_cls, err, tb = exc_info

        if err_cls is None:
            error_type = None
            error_str = None
            traceback_str = None
        else:
            if err_cls.__module__ == "builtins":
                error_type = err_cls.__name__
            else:
                error_type = "{module}.{name}".format(module=err_cls.__module__, name=err_cls.__name__)
            error_str = str(err)
            traceback_str = ''.join(traceback.format_tb(tb))

        trace_value = {}
        if details:
            trace_value["details"] = details
        trace_value.update({
            "error_type": error_type,
            "error_str": error_str,
            "traceback": traceback_str,
        })
        self.set_property(key, trace_value)
        return self

    def new(self) -> "MetricsLogger":
        return MetricsLogger(
            self.resolve_environment, self.context.create_copy_with_context()
        )
