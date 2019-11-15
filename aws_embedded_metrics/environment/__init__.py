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
