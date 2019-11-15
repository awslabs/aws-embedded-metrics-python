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

from aws_embedded_metrics.sinks import SocketClient
import logging
import socket
from urllib.parse import ParseResult

log = logging.getLogger(__name__)


class UdpClient(SocketClient):
    def __init__(self, endpoint: ParseResult):
        self.endpoint = endpoint

    def send_message(self, message: bytes) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message, (self.endpoint.hostname, self.endpoint.port))
        sock.close()
        log.info("Submitted metrics to agent over UDP.")
