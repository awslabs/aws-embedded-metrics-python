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
import threading
from urllib.parse import ParseResult

log = logging.getLogger(__name__)

# TODO: use non-blocking sockets or asyncore


class TcpClient(SocketClient):
    def __init__(self, endpoint: ParseResult):
        self._endpoint = endpoint
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._write_lock = threading.Lock()
        self._should_connect = True

    def connect(self) -> "TcpClient":
        try:
            self._sock.connect((self._endpoint.hostname, self._endpoint.port))
            self._should_connect = False
        except socket.timeout as e:
            log.error("Socket timeout durring connect %s" % (e,))
            self._should_connect = True
        except Exception as e:
            log.error("Failed to connect to the socket. %s" % (e,))
            self._should_connect = True
        return self

    def send_message(self, message: bytes) -> None:
        if self._sock._closed or self._should_connect:  # type: ignore
            self.connect()

        with self._write_lock:
            try:
                self._sock.sendall(message)
                log.info("Submitted metrics to agent over TCP.")
            except socket.timeout as e:
                log.error("Socket timeout durring send %s" % (e,))
                self.connect()
            except socket.error as e:
                log.error("Failed to write metrics to the socket due to socket.error. %s" % (e,))
                self.connect()
            except Exception as e:
                log.error("Failed to write metrics to the socket due to exception. %s" % (e,))
                self.connect()
