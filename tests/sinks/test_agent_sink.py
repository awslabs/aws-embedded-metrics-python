from aws_embedded_metrics.sinks.agent_sink import AgentSink
from aws_embedded_metrics.config import get_config

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
