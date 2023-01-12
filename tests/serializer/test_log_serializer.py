from aws_embedded_metrics.config import get_config
from aws_embedded_metrics.exceptions import DimensionSetExceededError
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.serializers.log_serializer import LogSerializer
from aws_embedded_metrics.storageResolution import StorageResolution
from collections import Counter
from faker import Faker
import json
import pytest

fake = Faker()

serializer = LogSerializer()


def test_serialize_dimensions():
    # arrange
    expected_key = fake.word()
    expected_value = fake.word()
    dimensions = {}
    dimensions[expected_key] = expected_value

    expected = {**get_empty_payload(), **dimensions}
    expected["_aws"]["CloudWatchMetrics"][0]["Dimensions"].append([expected_key])

    context = get_context()
    context.put_dimensions(dimensions)

    # act
    result_json = serializer.serialize(context)[0]

    # assert
    assert_json_equality(result_json, expected)


def test_serialize_properties():
    # arrange
    expected_key = fake.word()
    expected_value = fake.word()

    expected = {**get_empty_payload()}
    expected[expected_key] = expected_value

    context = get_context()
    context.set_property(expected_key, expected_value)

    # act
    result_json = serializer.serialize(context)[0]

    # assert
    assert_json_equality(result_json, expected)


def test_default_and_custom_dimensions_combined_limit_exceeded():
    # While serializing default dimensions are added to the custom dimension set,
    # and the combined size of the dimension set should not be more than 30
    dimensions = {}
    default_dimension_key = fake.word()
    default_dimension_value = fake.word()
    custom_dimensions_to_add = 30

    for i in range(0, custom_dimensions_to_add):
        dimensions[f"{i}"] = fake.word()

    context = get_context()
    context.set_default_dimensions({default_dimension_key: default_dimension_value})
    context.put_dimensions(dimensions)

    with pytest.raises(DimensionSetExceededError):
        serializer.serialize(context)


def test_serialize_metrics():
    # arrange
    expected_key = fake.word()
    expected_value = fake.random.randrange(0, 100)

    expected_metric_definition = {"Name": expected_key, "Unit": "None"}

    expected = {**get_empty_payload()}
    expected[expected_key] = expected_value
    expected["_aws"]["CloudWatchMetrics"][0]["Metrics"].append(
        expected_metric_definition
    )

    context = get_context()
    context.put_metric(expected_key, expected_value)

    # act
    result_json = serializer.serialize(context)[0]

    # assert
    assert_json_equality(result_json, expected)


def test_serialize_metrics_with_Standard_storageResolution():
    # arrange
    expected_key = fake.word()
    expected_value = fake.random.randrange(0, 100)

    expected_metric_definition = {"Name": expected_key, "Unit": "None"}

    expected = {**get_empty_payload()}
    expected[expected_key] = expected_value
    expected["_aws"]["CloudWatchMetrics"][0]["Metrics"].append(
        expected_metric_definition
    )

    context = get_context()
    context.put_metric(expected_key, expected_value, "None", StorageResolution.STANDARD)

    # act
    result_json = serializer.serialize(context)[0]

    # assert
    assert_json_equality(result_json, expected)


def test_serialize_metrics_with_High_storageResolution():
    # arrange
    expected_key = fake.word()
    expected_value = fake.random.randrange(0, 100)

    expected_metric_definition = {"Name": expected_key, "Unit": "None", "StorageResolution": 1}

    expected = {**get_empty_payload()}
    expected[expected_key] = expected_value
    expected["_aws"]["CloudWatchMetrics"][0]["Metrics"].append(
        expected_metric_definition
    )

    context = get_context()
    context.put_metric(expected_key, expected_value, "None", StorageResolution.HIGH)

    # act
    result_json = serializer.serialize(context)[0]

    # assert
    assert_json_equality(result_json, expected)


def test_serialize_more_than_100_metrics():
    # arrange
    expected_value = fake.random.randrange(0, 100)
    expected_batches = 3
    metrics = 295

    context = get_context()
    for index in range(metrics):
        expected_key = f"Metric-{index}"
        context.put_metric(expected_key, expected_value)

    # act
    results = serializer.serialize(context)

    # assert
    assert len(results) == expected_batches

    metric_index = 0
    for batch_index in range(expected_batches):
        expected_metric_count = metrics % 100 if (batch_index == expected_batches - 1) else 100
        result_json = results[batch_index]
        result_obj = json.loads(result_json)
        assert len(result_obj["_aws"]["CloudWatchMetrics"][0]["Metrics"]) == expected_metric_count

        for index in range(expected_metric_count):
            assert result_obj[f"Metric-{metric_index}"] == expected_value
            metric_index += 1


def test_serialize_more_than_100_datapoints():
    expected_batches = 3
    datapoints = 295
    metrics = 3

    context = get_context()
    for index in range(metrics):
        expected_key = f"Metric-{index}"
        for i in range(datapoints):
            context.put_metric(expected_key, i)

    # add one metric with more datapoints
    expected_extra_batches = 2
    extra_datapoints = 433
    for i in range(extra_datapoints):
        context.put_metric(f"Metric-{metrics}", i)

    # act
    results = serializer.serialize(context)

    # assert
    assert len(results) == expected_batches + expected_extra_batches

    for batch_index in range(expected_batches):
        result_json = results[batch_index]
        result_obj = json.loads(result_json)
        for index in range(metrics):
            metric_name = f"Metric-{index}"
            expected_datapoint_count = datapoints % 100 if (batch_index == expected_batches - 1) else 100
            assert len(result_obj[metric_name]) == expected_datapoint_count

    # extra metric with more datapoints
    for batch_index in range(expected_batches):
        result_json = results[batch_index]
        result_obj = json.loads(result_json)
        metric_name = f"Metric-{metrics}"
        expected_datapoint_count = extra_datapoints % 100 if (batch_index == expected_batches + expected_extra_batches - 1) else 100
        assert len(result_obj[metric_name]) == expected_datapoint_count


def test_serialize_with_more_than_100_metrics_and_datapoints():
    expected_batches = 11
    datapoints = 295
    metrics = 295

    expected_results = {}
    metric_results = {}
    context = get_context()
    for index in range(metrics):
        expected_key = f"Metric-{index}"
        expected_results[expected_key] = []
        metric_results[expected_key] = []

        for i in range(datapoints):
            context.put_metric(expected_key, i)
            expected_results[expected_key].append(i)

    # act
    results = serializer.serialize(context)

    # assert
    assert len(results) == expected_batches

    datapoints_count = Counter()
    for batch in results:
        result = json.loads(batch)
        datapoints_count.update({
            metric: len(result[metric])
            for metric in result if metric != "_aws"
        })
        for metric in result:
            if metric != "_aws":
                metric_results[metric] += result[metric]

    for count in datapoints_count.values():
        assert count == datapoints
    assert len(datapoints_count) == metrics
    assert metric_results == expected_results


def test_serialize_with_multiple_metrics():
    # arrange
    metrics = 2
    expected = {**get_empty_payload()}
    context = get_context()

    for index in range(metrics):
        expected_key = f"Metric-{index}"
        expected_value = fake.random.randrange(0, 100)
        context.put_metric(expected_key, expected_value)

        expected_metric_definition = {"Name": expected_key, "Unit": "None"}
        expected[expected_key] = expected_value
        expected["_aws"]["CloudWatchMetrics"][0]["Metrics"].append(
            expected_metric_definition
        )

    # act
    results = serializer.serialize(context)

    # assert
    assert len(results) == 1
    assert results == [json.dumps(expected)]


def test_serialize_metrics_with_multiple_datapoints():
    # arrange
    expected_key = fake.word()
    expected_values = [fake.random.randrange(0, 100), fake.random.randrange(0, 100)]
    expected_metric_definition = {"Name": expected_key, "Unit": "None"}
    expected = {**get_empty_payload()}
    expected[expected_key] = expected_values
    expected["_aws"]["CloudWatchMetrics"][0]["Metrics"].append(
        expected_metric_definition
    )

    context = get_context()
    for expected_value in expected_values:
        context.put_metric(expected_key, expected_value)

    # act
    results = serializer.serialize(context)

    # assert
    assert len(results) == 1
    assert results == [json.dumps(expected)]


def test_serialize_metrics_with_aggregation_disabled():
    """Test log records don't contain metadata when aggregation is disabled."""
    # arrange
    config = get_config()
    config.disable_metric_extraction = True

    expected_key = fake.word()
    expected_value = fake.random.randrange(0, 100)

    expected = {expected_key: expected_value}

    context = get_context()
    context.put_metric(expected_key, expected_value)

    # act
    result_json = serializer.serialize(context)[0]

    # assert
    assert_json_equality(result_json, expected)


# Test utility method


def get_context():
    context = MetricsContext.empty()
    context.meta["Timestamp"] = 0
    return context


def get_empty_payload():
    return {
        "_aws": {
            "Timestamp": 0,
            "CloudWatchMetrics": [
                {"Dimensions": [], "Metrics": [], "Namespace": "aws-embedded-metrics"}
            ],
        }
    }


def assert_json_equality(actual_json, expected_obj):
    actual_obj = json.loads(actual_json)
    print("Expected: ", expected_obj)
    print("Actual: ", actual_obj)
    assert actual_obj == expected_obj
