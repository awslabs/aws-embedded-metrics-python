from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.sinks.agent_sink import AgentSink
from aws_embedded_metrics.config import get_config
from unittest.mock import patch, Mock


Config = get_config()


def test_default_endpoint():
    # arrange
    expected_hostname = "0.0.0.0"
    expected_protocol = "tcp"
    expected_port = 25888

    #  act
    sink = AgentSink("logGroup")

    # assert
    assert sink.endpoint.hostname == expected_hostname
    assert sink.endpoint.port == expected_port
    assert sink.endpoint.scheme == expected_protocol


def test_can_parse_udp_endpoints():
    # arrange
    provided = "udp://127.0.0.1:10000"
    expected_hostname = "127.0.0.1"
    expected_protocol = "udp"
    expected_port = 10000

    Config.agent_endpoint = provided

    # act
    sink = AgentSink("logGroup")

    # assert
    assert sink.endpoint.hostname == expected_hostname
    assert sink.endpoint.port == expected_port
    assert sink.endpoint.scheme == expected_protocol


def test_can_parse_tcp_endpoints():
    # arrange
    provided = "tcp://127.0.0.1:10000"
    expected_hostname = "127.0.0.1"
    expected_protocol = "tcp"
    expected_port = 10000

    Config.agent_endpoint = provided

    # act
    sink = AgentSink("logGroup")

    # assert
    assert sink.endpoint.hostname == expected_hostname
    assert sink.endpoint.port == expected_port
    assert sink.endpoint.scheme == expected_protocol


def test_fallback_to_default_endpoint_on_parse_failure():
    # arrange
    expected_hostname = "0.0.0.0"
    expected_protocol = "tcp"
    expected_port = 25888

    Config.agent_endpoint = "this is not a valid URI"

    # act
    sink = AgentSink("logGroup")

    # assert
    assert sink.endpoint.hostname == expected_hostname
    assert sink.endpoint.port == expected_port
    assert sink.endpoint.scheme == expected_protocol


@patch("aws_embedded_metrics.sinks.agent_sink.get_socket_client")
def test_more_than_max_number_of_metrics(mock_get_socket_client):
    # arrange
    context = MetricsContext.empty()
    expected_metrics = 401
    expected_send_message_calls = 5
    for index in range(expected_metrics):
        context.put_metric(f"{index}", 1)

    mock_tcp_client = Mock()
    mock_get_socket_client.return_value = mock_tcp_client

    # act
    sink = AgentSink("")
    sink.accept(context)

    # assert
    assert expected_send_message_calls == mock_tcp_client.send_message.call_count
