from aws_embedded_metrics import config
from aws_embedded_metrics.logger import metrics_logger
from aws_embedded_metrics.sinks import Sink
from aws_embedded_metrics.environment import Environment
import pytest
from faker import Faker
from asyncio import Future
from importlib import reload
import os

fake = Faker()

# These tests write data using the logger, flush and then
# make assertions against the state that was flushed to
# the mock sink


@pytest.mark.asyncio
async def test_can_set_property(mocker):
    # arrange
    expected_key = fake.word()
    expected_value = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.set_property(expected_key, expected_value)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    assert context.properties[expected_key] == expected_value


@pytest.mark.asyncio
async def test_can_put_metric(mocker):
    # arrange
    expected_key = fake.word()
    expected_value = fake.random.randrange(100)

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.put_metric(expected_key, expected_value)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    assert context.metrics[expected_key].values == [expected_value]
    assert context.metrics[expected_key].unit == "None"


@pytest.mark.asyncio
async def test_put_metric_appends_values_to_array(mocker):
    # arrange
    expected_key = fake.word()
    expected_value_1 = fake.random.randrange(100)
    expected_value_2 = fake.random.randrange(100)

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.put_metric(expected_key, expected_value_1)
    logger.put_metric(expected_key, expected_value_2)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    assert context.metrics[expected_key].values == [expected_value_1, expected_value_2]


@pytest.mark.asyncio
async def test_put_dimension(mocker):
    # arrange
    expected_key = fake.word()
    expected_value = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.put_dimensions({expected_key: expected_value})
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    dimensions = context.get_dimensions()
    assert len(dimensions) == 1
    assert dimensions[0][expected_key] == expected_value


@pytest.mark.asyncio
async def test_logger_configures_default_dimensions_on_flush(before, mocker):
    # arrange
    log_group_name = fake.word()
    service_name = fake.word()
    service_type = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    env.get_log_group_name.return_value = log_group_name
    env.get_name.return_value = service_name
    env.get_type.return_value = service_type

    # act
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    assert context.default_dimensions["LogGroup"] == log_group_name
    assert context.default_dimensions["ServiceName"] == service_name
    assert context.default_dimensions["ServiceType"] == service_type


@pytest.mark.asyncio
async def test_logger_configures_uses_config_overrides_for_default_dimensions(mocker):
    # arrange
    log_group_name = fake.word()
    service_name = fake.word()
    service_type = fake.word()

    os.environ["AWS_EMF_SERVICE_NAME"] = service_name
    os.environ["AWS_EMF_SERVICE_TYPE"] = service_type

    logger, sink, env = get_logger_and_sink(mocker)

    env.get_log_group_name.return_value = log_group_name
    env.get_name.return_value = "this-should-not-be-returned"
    env.get_type.return_value = "this-should-not-be-returned"

    # act
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    assert len(context.default_dimensions) == 3
    assert context.default_dimensions["LogGroup"] == log_group_name
    assert context.default_dimensions["ServiceName"] == service_name
    assert context.default_dimensions["ServiceType"] == service_type


@pytest.mark.asyncio
async def test_set_dimensions_overrides_all_dimensions(mocker):
    # arrange
    logger, sink, env = get_logger_and_sink(mocker)

    # setup the typical default dimensions
    env.get_log_group_name.return_value = fake.word()
    env.get_name.return_value = fake.word()
    env.get_type.return_value = fake.word()

    expected_key = fake.word()
    expected_value = fake.word()

    # act
    logger.set_dimensions({expected_key: expected_value})
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    dimension_sets = context.get_dimensions()
    assert len(dimension_sets) == 1
    dimensions = dimension_sets[0]
    assert len(dimensions) == 1
    assert dimensions[expected_key] == expected_value


@pytest.mark.asyncio
async def test_can_set_namespace(mocker):
    # arrange
    expected_value = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.set_namespace(expected_value)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    assert context.namespace == expected_value


@pytest.mark.asyncio
async def test_context_is_preserved_across_flushes(mocker):
    # arrange
    expected_namespace = "Namespace"
    metric_key = "Metric"
    expected_dimension_key = "Dim"
    expected_property_key = "Prop"
    expected_value = "Value"

    logger, sink, env = get_logger_and_sink(mocker)

    logger.set_namespace(expected_namespace)
    logger.set_property(expected_property_key, expected_value)
    logger.set_dimensions({expected_dimension_key: expected_value})

    # act
    logger.put_metric(metric_key, 0)
    await logger.flush()

    context = sink.accept.call_args[0][0]
    assert context.namespace == expected_namespace
    assert context.properties[expected_property_key] == expected_value
    assert context.metrics[metric_key].values == [0]

    logger.put_metric(metric_key, 1)
    await logger.flush()

    context = sink.accept.call_args[0][0]
    assert context.namespace == expected_namespace
    assert context.properties[expected_property_key] == expected_value
    assert context.metrics[metric_key].values == [1]


# Test helper methods


@pytest.fixture
def before():
    os.environ["AWS_EMF_SERVICE_NAME"] = ""
    os.environ["AWS_EMF_SERVICE_TYPE"] = ""
    os.environ["AWS_EMF_LOG_GROUP_NAME"] = ""


def get_logger_and_sink(mocker):
    env = mocker.create_autospec(spec=Environment)

    def env_provider():
        result_future = Future()
        result_future.set_result(env)
        return result_future

    sink = mocker.create_autospec(spec=Sink)
    env.get_sink.return_value = sink

    # reload modules to force reload of configuration
    reload(config)
    reload(metrics_logger)

    return (metrics_logger.MetricsLogger(env_provider), sink, env)


def get_flushed_context(sink):
    sink.accept.assert_called_once()
    context = sink.accept.call_args[0][0]
    return context
