from aws_embedded_metrics.sinks.tcp_client import TcpClient
from urllib.parse import urlparse
import socket
import threading
import time
import logging

log = logging.getLogger(__name__)

test_host = '0.0.0.0'
test_port = 9999
endpoint = urlparse("tcp://0.0.0.0:9999")
message = "_16-Byte-String_".encode('utf-8')


def test_can_send_message():
    # arrange
    agent = InProcessAgent().start()
    client = TcpClient(endpoint)

    # act
    client.connect()
    client.send_message(message)

    # assert
    time.sleep(1)
    messages = agent.messages
    assert 1 == len(messages)
    assert message == messages[0]
    agent.shutdown()


def test_can_connect_concurrently_from_threads():
    # arrange
    concurrency = 10
    agent = InProcessAgent().start()
    client = TcpClient(endpoint)
    barrier = threading.Barrier(concurrency, timeout=5)

    def run():
        barrier.wait()
        client.connect()
        client.send_message(message)

    def start_thread():
        thread = threading.Thread(target=run, args=())
        thread.daemon = True
        thread.start()

    # act
    for _ in range(concurrency):
        start_thread()

    # assert
    time.sleep(1)
    messages = agent.messages
    assert concurrency == len(messages)
    for i in range(concurrency):
        assert message == messages[i]
    agent.shutdown()


def test_can_recover_from_agent_shutdown():
    # arrange
    agent = InProcessAgent().start()
    client = TcpClient(endpoint)

    # act
    client.connect()
    client.send_message(message)
    agent.shutdown()
    time.sleep(5)
    client.send_message(message)
    agent = InProcessAgent().start()
    client.send_message(message)

    # assert
    time.sleep(1)
    messages = agent.messages
    assert 1 == len(messages)
    assert message == messages[0]
    agent.shutdown()


class InProcessAgent(object):
    """ Agent that runs on a background thread and collects
        messages in memory.
    """

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((test_host, test_port))
        self.sock.listen()
        self.is_shutdown = False
        self.messages = []

    def start(self) -> "InProcessAgent":
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
        return self

    def run(self):
        while not self.is_shutdown:
            connection, client_address = self.sock.accept()
            self.connection = connection

            try:
                while not self.is_shutdown:
                    data = self.connection.recv(16)
                    if data:
                        self.messages.append(data)
                    else:
                        break
            finally:
                log.error("Exited the recv loop")

    def shutdown(self):
        try:
            self.is_shutdown = True
            if hasattr(self, 'connection'):
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
            self.sock.close()
        except Exception as e:
            log.error("Failed to shutdown %s" % (e,))
