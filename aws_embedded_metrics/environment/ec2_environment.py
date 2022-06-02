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
from aws_embedded_metrics.sinks.agent_sink import AgentSink
from typing import Any, Dict, Optional, cast

import aiohttp
import logging


log = logging.getLogger(__name__)
Config = get_config()

# Documentation for configuring instance metadata can be found here:
# https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html
TOKEN_ENDPOINT = "http://169.254.169.254/latest/api/token"
TOKEN_REQUEST_HEADER_KEY = "X-aws-ec2-metadata-token-ttl-seconds"
TOKEN_REQUEST_HEADER_VALUE = "21600"
DEFAULT_EC2_METADATA_ENDPOINT = (
    "http://169.254.169.254/latest/dynamic/instance-identity/document"
)
METADATA_REQUEST_HEADER_KEY = "X-aws-ec2-metadata-token"


async def fetchJSON(
    session: aiohttp.ClientSession, method: str, url: str, headers: Dict[str, str],
) -> Dict[str, Any]:
    async with session.request(method, url, timeout=2, headers=headers) as response:
        # content_type=None prevents validation of the HTTP Content-Type header
        # The EC2 metadata endpoint uses text/plain instead of application/json
        # https://github.com/aio-libs/aiohttp/blob/7f777333a4ec0043ddf2e8d67146a626089773d9/aiohttp/web_request.py#L582-L585
        return cast(Dict[str, Any], await response.json(content_type=None))


async def fetchString(
    session: aiohttp.ClientSession, method: str, url: str, headers: Dict[str, str]
) -> str:
    async with session.request(method, url, timeout=2, headers=headers) as response:
        return await response.text()


class EC2Environment(Environment):
    def __init__(self) -> None:
        self.sink: Optional[AgentSink] = None

    async def probe(self) -> bool:
        async with aiohttp.ClientSession() as session:
            metadata_endpoint = (
                Config.ec2_metadata_endpoint or DEFAULT_EC2_METADATA_ENDPOINT
            )
            token_header = {TOKEN_REQUEST_HEADER_KEY: TOKEN_REQUEST_HEADER_VALUE}
            log.info("Fetching token for EC2 metadata request from: %s", TOKEN_ENDPOINT)
            try:
                token = await fetchString(session, "PUT", TOKEN_ENDPOINT, token_header)
                log.debug("Received token for request to EC2 metadata endpoint.")
            except Exception:
                log.info(
                    "Failed to fetch token for EC2 metadata request from %s", TOKEN_ENDPOINT
                )
                return False

            log.info("Fetching EC2 metadata from: %s", metadata_endpoint)
            try:
                metadata_request_header = {METADATA_REQUEST_HEADER_KEY: token}
                response_json = await fetchJSON(session, "GET", metadata_endpoint, metadata_request_header)
                log.debug("Received response from EC2 metadata endpoint.")
                self.metadata = response_json
                return True
            except Exception:
                log.info(
                    "Failed to connect to EC2 metadata endpoint %s", metadata_endpoint
                )
            return False

    def get_name(self) -> str:
        return Config.service_name or "Unknown"

    def get_type(self) -> str:
        if self.metadata is not None:
            return "AWS::EC2::Instance"

        return "Unknown"

    def get_log_group_name(self) -> str:
        return Config.log_group_name or f"{self.get_name()}-metrics"

    def configure_context(self, context: MetricsContext) -> None:
        if self.metadata is not None:
            context.set_property("imageId", self.metadata["imageId"])
            context.set_property("instanceId", self.metadata["instanceId"])
            context.set_property("instanceType", self.metadata["instanceType"])
            context.set_property("privateIp", self.metadata["privateIp"])
            context.set_property("availabilityZone", self.metadata["availabilityZone"])

    def get_sink(self) -> AgentSink:
        if self.sink is None:
            self.sink = AgentSink(self.get_log_group_name(), Config.log_stream_name)
        return self.sink
