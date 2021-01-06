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

from aws_embedded_metrics.config import get_config
from aws_embedded_metrics.environment import Environment
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.sinks import Sink
from aws_embedded_metrics.sinks.stdout_sink import StdoutSink
from typing import Optional

Config = get_config()


class LocalEnvironment(Environment):
    def __init__(self) -> None:
        self.sink: Optional[Sink] = None

    async def probe(self) -> bool:
        return False

    def get_name(self) -> str:
        return Config.service_name or "Unknown"

    def get_type(self) -> str:
        return Config.service_type or "Unknown"

    def get_log_group_name(self) -> str:
        return Config.log_group_name or f"{self.get_name()}-metrics"

    def configure_context(self, context: MetricsContext) -> None:
        pass

    def get_sink(self) -> Sink:
        if self.sink is None:
            self.sink = StdoutSink()
        return self.sink
