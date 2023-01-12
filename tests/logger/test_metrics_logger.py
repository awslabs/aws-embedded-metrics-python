from aws_embedded_metrics import config
from aws_embedded_metrics.logger import metrics_logger
from aws_embedded_metrics.sinks import Sink
from aws_embedded_metrics.environment import Environment
from aws_embedded_metrics.exceptions import InvalidNamespaceError, InvalidMetricError
from aws_embedded_metrics.storageResolution import StorageResolution
import aws_embedded_metrics.constants as constants
import pytest
from faker import Faker
from asyncio import Future
from importlib import reload
import os
import sys

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
async def test_can_put_metric_with_different_storage_resolution_different_flush(mocker):
    # arrange
    expected_key = fake.word()
    expected_value = fake.random.randrange(100)
    metric_storageResolution = StorageResolution.HIGH

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.put_metric(expected_key, expected_value, None, metric_storageResolution)
    await logger.flush()

    # assert
    context = sink.accept.call_args[0][0]
    assert context.metrics[expected_key].values == [expected_value]
    assert context.metrics[expected_key].unit == "None"
    assert context.metrics[expected_key].storageResolution == metric_storageResolution

    expected_key = fake.word()
    expected_value = fake.random.randrange(100)
    logger.put_metric(expected_key, expected_value, None)
    await logger.flush()
    context = sink.accept.call_args[0][0]
    assert context.metrics[expected_key].values == [expected_value]
    assert context.metrics[expected_key].unit == "None"
    assert context.metrics[expected_key].storageResolution == StorageResolution.STANDARD


@pytest.mark.asyncio
async def test_cannot_put_metric_with_different_storage_resolution_same_flush(mocker):
    # arrange
    expected_key = fake.word()
    expected_value = fake.random.randrange(100)

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.put_metric(expected_key, expected_value, None, StorageResolution.HIGH)
    with pytest.raises(InvalidMetricError):
        logger.put_metric(expected_key, expected_value, None, StorageResolution.STANDARD)
        await logger.flush()


@pytest.mark.asyncio
async def test_can_add_stack_trace(mocker):
    # arrange
    expected_key = fake.word()
    expected_details = fake.word()
    expected_error_str = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    from configparser import Error  # Just some non-builtin exception

    # act
    try:
        raise Error(expected_error_str)
    except Error:
        logger.add_stack_trace(expected_key, expected_details)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    value = context.properties[expected_key]
    assert isinstance(value, dict)
    assert value["details"] == expected_details
    assert value["error_type"] == "configparser.Error"
    assert value["error_str"] == expected_error_str
    assert value["traceback"].split("\n")[-2] == "    raise Error(expected_error_str)"


@pytest.mark.asyncio
async def test_can_add_stack_trace_for_builtin(mocker):
    # arrange
    expected_key = fake.word()
    expected_details = fake.word()
    expected_error_str = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    try:
        raise ValueError(expected_error_str)
    except ValueError:
        logger.add_stack_trace(expected_key, expected_details)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    value = context.properties[expected_key]
    assert isinstance(value, dict)
    assert value["details"] == expected_details
    assert value["error_type"] == "ValueError"
    assert value["error_str"] == expected_error_str
    assert value["traceback"].split("\n")[-2] == "    raise ValueError(expected_error_str)"


@pytest.mark.asyncio
async def test_can_add_empty_stack_trace(mocker):
    # arrange
    expected_key = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.add_stack_trace(expected_key)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    value = context.properties[expected_key]
    assert isinstance(value, dict)
    assert "value" not in value
    assert value["error_type"] is None
    assert value["error_str"] is None
    assert value["traceback"] is None


@pytest.mark.asyncio
async def test_can_add_stack_trace_manually(mocker):
    # arrange
    expected_key = fake.word()
    expected_details = fake.word()
    expected_error_str = fake.word()

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    try:
        raise ValueError(expected_error_str)
    except ValueError:
        exc_info = sys.exc_info()
    logger.add_stack_trace(expected_key, expected_details, exc_info=exc_info)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    value = context.properties[expected_key]
    assert isinstance(value, dict)
    assert value["details"] == expected_details
    assert value["error_type"] == "ValueError"
    assert value["error_str"] == expected_error_str
    assert value["traceback"].split("\n")[-2] == "    raise ValueError(expected_error_str)"


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
async def test_reset_dimension_with_default_dimension(mocker):
    # arrange
    pair1 = ["key1", "val1"]
    pair2 = ["key2", "val2"]

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.put_dimensions({pair1[0]: pair1[1]})
    logger.reset_dimensions(True)
    logger.put_dimensions({pair2[0]: pair2[1]})
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    dimensions = context.get_dimensions()
    assert len(dimensions) == 1
    assert len(dimensions[0]) == 4
    assert dimensions[0][pair2[0]] == pair2[1]


@pytest.mark.asyncio
async def test_reset_dimension_without_default_dimension(mocker):
    # arrange
    pair1 = ["key1", "val1"]
    pair2 = ["key2", "val2"]

    logger, sink, env = get_logger_and_sink(mocker)

    # act
    logger.put_dimensions({pair1[0]: pair1[1]})
    logger.reset_dimensions(False)
    logger.put_dimensions({pair2[0]: pair2[1]})
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    dimensions = context.get_dimensions()
    assert len(dimensions) == 1
    assert len(dimensions[0]) == 1
    assert dimensions[0][pair2[0]] == pair2[1]


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
async def test_configure_set_dimensions_to_preserve_default_dimensions(mocker):
    # arrange
    logger, sink, env = get_logger_and_sink(mocker)

    # setup the typical default dimensions
    env.get_log_group_name.return_value = fake.word()
    env.get_name.return_value = fake.word()
    env.get_type.return_value = fake.word()

    expected_key = fake.word()
    expected_value = fake.word()

    # act
    logger.set_dimensions({expected_key: expected_value}, use_default=True)
    await logger.flush()

    # assert
    context = get_flushed_context(sink)
    dimension_sets = context.get_dimensions()
    assert len(dimension_sets) == 1
    dimensions = dimension_sets[0]
    assert len(dimensions) == 4
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


@pytest.mark.parametrize("namespace", [None, "", " ", "a" * (constants.MAX_NAMESPACE_LENGTH + 1), "ŋàɱȅƨƥȁƈȅ", "namespace "])
def test_set_invalid_namespace_throws_exception(namespace, mocker):
    logger, sink, env = get_logger_and_sink(mocker)

    with pytest.raises(InvalidNamespaceError):
        logger.set_namespace(namespace)


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


@pytest.mark.asyncio
async def test_flush_dont_preserve_dimensions_by_default(mocker):
    # arrange
    dimension_key = "Dim"
    dimension_value = "Value"

    logger, sink, env = get_logger_and_sink(mocker)

    logger.set_dimensions({dimension_key: dimension_value})

    # act
    await logger.flush()

    context = sink.accept.call_args[0][0]
    dimensions = context.get_dimensions()
    assert len(dimensions) == 1
    assert dimensions[0][dimension_key] == dimension_value

    await logger.flush()

    context = sink.accept.call_args[0][0]
    dimensions = context.get_dimensions()
    assert len(dimensions) == 1
    assert dimension_key not in dimensions[0]


@pytest.mark.asyncio
async def test_configure_flush_to_preserve_dimensions(mocker):
    # arrange
    dimension_key = "Dim"
    dimension_value = "Value"

    logger, sink, env = get_logger_and_sink(mocker)

    logger.set_dimensions({dimension_key: dimension_value})
    logger.flush_preserve_dimensions = True

    # act
    await logger.flush()

    context = sink.accept.call_args[0][0]
    dimensions = context.get_dimensions()
    assert len(dimensions) == 1
    assert dimensions[0][dimension_key] == dimension_value

    await logger.flush()

    context = sink.accept.call_args[0][0]
    dimensions = context.get_dimensions()
    assert len(dimensions) == 1
    assert dimensions[0][dimension_key] == dimension_value


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
