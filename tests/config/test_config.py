from aws_embedded_metrics import config
from faker import Faker
import os
from importlib import reload


fake = Faker()


def get_config():
    # reload the configuration module since it is loaded on
    # startup and cached
    reload(config)
    return config.get_config()


def test_can_get_config_from_environment():
    # arrange
    debug_enabled = True
    service_name = fake.word()
    service_type = fake.word()
    log_group = fake.word()
    log_stream = fake.word()
    agent_endpoint = fake.word()

    os.environ["AWS_EMF_ENABLE_DEBUG_LOGGING"] = str(debug_enabled)
    os.environ["AWS_EMF_SERVICE_NAME"] = service_name
    os.environ["AWS_EMF_SERVICE_TYPE"] = service_type
    os.environ["AWS_EMF_LOG_GROUP_NAME"] = log_group
    os.environ["AWS_EMF_LOG_STREAM_NAME"] = log_stream
    os.environ["AWS_EMF_AGENT_ENDPOINT"] = agent_endpoint

    # act
    result = get_config()

    # assert
    assert result.debug_logging_enabled == debug_enabled
    assert result.service_name == service_name
    assert result.service_type == service_type
    assert result.log_group_name == log_group
    assert result.log_stream_name == log_stream
    assert result.agent_endpoint == agent_endpoint


def test_can_override_config():
    # arrange
    os.environ["AWS_EMF_ENABLE_DEBUG_LOGGING"] = str(True)
    os.environ["AWS_EMF_SERVICE_NAME"] = fake.word()
    os.environ["AWS_EMF_SERVICE_TYPE"] = fake.word()
    os.environ["AWS_EMF_LOG_GROUP_NAME"] = fake.word()
    os.environ["AWS_EMF_LOG_STREAM_NAME"] = fake.word()
    os.environ["AWS_EMF_AGENT_ENDPOINT"] = fake.word()

    config = get_config()

    debug_enabled = False
    service_name = fake.word()
    service_type = fake.word()
    log_group = fake.word()
    log_stream = fake.word()
    agent_endpoint = fake.word()

    # act
    config.debug_logging_enabled = debug_enabled
    config.service_name = service_name
    config.service_type = service_type
    config.log_group_name = log_group
    config.log_stream_name = log_stream
    config.agent_endpoint = agent_endpoint

    # assert
    assert config.debug_logging_enabled == debug_enabled
    assert config.service_name == service_name
    assert config.service_type == service_type
    assert config.log_group_name == log_group
    assert config.log_stream_name == log_stream
    assert config.agent_endpoint == agent_endpoint
