from aws_embedded_metrics import config
from faker import Faker
from importlib import reload


fake = Faker()


def get_config():
    # reload the configuration module since it is loaded on
    # startup and cached
    reload(config)
    return config.get_config()


def test_can_get_config_from_environment(monkeypatch):
    # arrange
    debug_enabled = True
    service_name = fake.word()
    service_type = fake.word()
    log_group = fake.word()
    log_stream = fake.word()
    agent_endpoint = fake.word()
    ec2_metadata_endpoint = fake.word()
    namespace = fake.word()
    disable_metric_extraction = True
    environment_override = fake.word()

    monkeypatch.setenv("AWS_EMF_ENABLE_DEBUG_LOGGING", str(debug_enabled))
    monkeypatch.setenv("AWS_EMF_SERVICE_NAME", service_name)
    monkeypatch.setenv("AWS_EMF_SERVICE_TYPE", service_type)
    monkeypatch.setenv("AWS_EMF_LOG_GROUP_NAME", log_group)
    monkeypatch.setenv("AWS_EMF_LOG_STREAM_NAME", log_stream)
    monkeypatch.setenv("AWS_EMF_AGENT_ENDPOINT", agent_endpoint)
    monkeypatch.setenv("AWS_EMF_EC2_METADATA_ENDPOINT", ec2_metadata_endpoint)
    monkeypatch.setenv("AWS_EMF_NAMESPACE", namespace)
    monkeypatch.setenv("AWS_EMF_DISABLE_METRIC_EXTRACTION", str(disable_metric_extraction))
    monkeypatch.setenv("AWS_EMF_ENVIRONMENT", environment_override)

    # act
    result = get_config()

    # assert
    assert result.debug_logging_enabled == debug_enabled
    assert result.service_name == service_name
    assert result.service_type == service_type
    assert result.log_group_name == log_group
    assert result.log_stream_name == log_stream
    assert result.agent_endpoint == agent_endpoint
    assert result.ec2_metadata_endpoint == ec2_metadata_endpoint
    assert result.namespace == namespace
    assert result.disable_metric_extraction == disable_metric_extraction
    assert result.environment == environment_override


def test_can_override_config(monkeypatch):
    # arrange
    monkeypatch.setenv("AWS_EMF_ENABLE_DEBUG_LOGGING", str(True))
    monkeypatch.setenv("AWS_EMF_SERVICE_NAME", fake.word())
    monkeypatch.setenv("AWS_EMF_SERVICE_TYPE", fake.word())
    monkeypatch.setenv("AWS_EMF_LOG_GROUP_NAME", fake.word())
    monkeypatch.setenv("AWS_EMF_LOG_STREAM_NAME", fake.word())
    monkeypatch.setenv("AWS_EMF_AGENT_ENDPOINT", fake.word())
    monkeypatch.setenv("AWS_EMF_EC2_METADATA_ENDPOINT", fake.word())
    monkeypatch.setenv("AWS_EMF_NAMESPACE", fake.word())
    monkeypatch.setenv("AWS_EMF_DISABLE_METRIC_EXTRACTION", str(True))
    monkeypatch.setenv("AWS_EMF_ENVIRONMENT", fake.word())

    config = get_config()

    debug_enabled = False
    service_name = fake.word()
    service_type = fake.word()
    log_group = fake.word()
    log_stream = fake.word()
    agent_endpoint = fake.word()
    ec2_metadata_endpoint = fake.word()
    namespace = fake.word()
    disable_metric_extraction = False
    environment = fake.word()

    # act
    config.debug_logging_enabled = debug_enabled
    config.service_name = service_name
    config.service_type = service_type
    config.log_group_name = log_group
    config.log_stream_name = log_stream
    config.agent_endpoint = agent_endpoint
    config.ec2_metadata_endpoint = ec2_metadata_endpoint
    config.namespace = namespace
    config.disable_metric_extraction = disable_metric_extraction
    config.environment = environment

    # assert
    assert config.debug_logging_enabled == debug_enabled
    assert config.service_name == service_name
    assert config.service_type == service_type
    assert config.log_group_name == log_group
    assert config.log_stream_name == log_stream
    assert config.agent_endpoint == agent_endpoint
    assert config.ec2_metadata_endpoint == ec2_metadata_endpoint
    assert config.namespace == namespace
    assert config.disable_metric_extraction == disable_metric_extraction
    assert config.environment == environment
