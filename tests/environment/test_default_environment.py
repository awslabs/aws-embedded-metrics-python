from aws_embedded_metrics.config import get_config
from aws_embedded_metrics.environment.default_environment import DefaultEnvironment
from aws_embedded_metrics.sinks.agent_sink import AgentSink
import pytest
from faker import Faker

fake = Faker()
Config = get_config()


@pytest.mark.asyncio
async def test_probe_always_returns_true():
    # arrange
    env = DefaultEnvironment()

    # act
    result = await env.probe()

    # assert
    assert result is True


def test_get_name_returns_unknown_if_not_specified():
    # arrange
    env = DefaultEnvironment()

    # act
    result = env.get_name()

    # assert
    assert result == "Unknown"


def test_get_type_returns_unknown_if_not_specified():
    # arrange
    env = DefaultEnvironment()

    # act
    result = env.get_type()

    # assert
    assert result == "Unknown"


def test_get_name_returns_name_if_configured():
    # arrange
    expected_name = fake.word()
    env = DefaultEnvironment()
    Config.service_name = expected_name

    # act
    result = env.get_name()

    # assert
    assert result == expected_name


def test__get_type__returns_type_if_configured():
    # arrange
    expected_type = fake.word()
    env = DefaultEnvironment()
    Config.service_type = expected_type

    # act
    result = env.get_type()

    # assert
    assert result == expected_type


def test__get_log_group_name__returns_log_group_if_configured():
    # arrange
    expected = fake.word()
    env = DefaultEnvironment()
    Config.log_group_name = expected

    # act
    result = env.get_log_group_name()

    # assert
    assert result == expected


def test__get_log_group_name__returns_service_name_metrics_if_not_configured():
    # arrange
    expected = fake.word()
    env = DefaultEnvironment()
    Config.service_name = expected
    Config.log_group_name = None

    # act
    result = env.get_log_group_name()

    # assert
    assert result == f"{expected}-metrics"


def test__get_sink__returns_agent_sink():
    # arrange
    env = DefaultEnvironment()

    # act
    result = env.get_sink()

    # assert
    assert isinstance(result, AgentSink)
