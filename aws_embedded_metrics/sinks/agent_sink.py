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
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.sinks import Sink
from aws_embedded_metrics.serializers import Serializer
from aws_embedded_metrics.serializers.log_serializer import LogSerializer
import logging
import socket
from urllib.parse import urlparse, ParseResult

log = logging.getLogger(__name__)
Config = get_config()

DEFAULT_ENDPOINT = urlparse("udp://0.0.0.0:25888")


def get_endpoint() -> ParseResult:
    if not Config.agent_endpoint:
        return DEFAULT_ENDPOINT
    try:
        parsed_url = urlparse(Config.agent_endpoint)
        if parsed_url is None or parsed_url.hostname is None or parsed_url.port is None:
            return DEFAULT_ENDPOINT
        else:
            return parsed_url
    except Exception:
        log.debug("Failed to parse agent endpoint: %s", Config.agent_endpoint)
        return DEFAULT_ENDPOINT


class AgentSink(Sink):
    def __init__(
        self,
        log_group_name: str,
        log_steam_name: str = None,
        serializer: Serializer = LogSerializer(),
    ):
        self.log_group_name = log_group_name
        self.log_steam_name = log_steam_name
        self.serializer = serializer
        self.endpoint = get_endpoint()

    def accept(self, context: MetricsContext) -> None:
        context.set_property("log_group_name", self.log_group_name)
        if self.log_steam_name is not None:
            context.set_property("log_stream_name", self.log_steam_name)

        serialized_content = self.serializer.serialize(context)
        log.info(
            "Parsed agent endpoint %s:%s", self.endpoint.hostname, self.endpoint.port
        )
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.sendto(
            serialized_content.encode(), (self.endpoint.hostname, self.endpoint.port)
        )
        udp_socket.close()
        log.info("Submitted metrics to agent over UDP.")

    @staticmethod
    def name() -> str:
        return "AgentSink"
