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
from aws_embedded_metrics.sinks import Sink
from aws_embedded_metrics.sinks.lambda_sink import LambdaSink
import os


def get_env(key: str) -> str:
    if key in os.environ:
        return os.environ[key]
    return ""


sink = LambdaSink()


class LambdaEnvironment(Environment):
    @staticmethod
    def probe() -> bool:
        return len(get_env("AWS_LAMBDA_FUNCTION_NAME")) > 0

    @staticmethod
    def get_name() -> str:
        return LambdaEnvironment.get_log_group_name()

    @staticmethod
    def get_type() -> str:
        return "AWS::Lambda::Function"

    @staticmethod
    def get_log_group_name() -> str:
        return get_env("AWS_LAMBDA_FUNCTION_NAME")

    @staticmethod
    def configure_context(context: MetricsContext) -> None:
        context.set_property("executionEnvironment", get_env("AWS_EXECUTION_ENV"))
        context.set_property("memorySize", get_env("AWS_LAMBDA_FUNCTION_MEMORY_SIZE"))
        context.set_property("functionVersion", get_env("AWS_LAMBDA_FUNCTION_VERSION"))
        context.set_property("logStreamId", get_env("AWS_LAMBDA_LOG_STREAM_NAME"))
        trace_id = get_env("_X_AMZN_TRACE_ID")

        if len(trace_id) > 0 and "Sampled=1" in trace_id:
            context.set_property("traceId", trace_id)

    @staticmethod
    def get_sink() -> Sink:
        """Create the appropriate sink for this environment."""
        return sink
