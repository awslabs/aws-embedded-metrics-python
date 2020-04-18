from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.serializers.log_serializer import LogSerializer
from faker import Faker
import json

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


def test_cannot_serialize_more_than_9_dimensions():
    # arrange
    dimensions = {}
    dimension_pointers = []
    allowed_dimensions = 9
    dimensions_to_add = 15

    for i in range(0, dimensions_to_add):
        print(i)
        expected_key = f"{i}"
        expected_value = fake.word()
        dimensions[expected_key] = expected_value
        dimension_pointers.append(expected_key)

    expected_dimensions_pointers = dimension_pointers[0:allowed_dimensions]

    expected = {**get_empty_payload(), **dimensions}
    expected["_aws"]["CloudWatchMetrics"][0]["Dimensions"].append(
        expected_dimensions_pointers
    )

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


def test_serialize_more_than_100_metrics():
    # arrange
    expected_value = fake.word()
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


def test_serialize_with_multiple_metrics():
    # arrange
    metrics = 2
    expected = {**get_empty_payload()}
    context = get_context()

    for index in range(metrics):
        expected_key = f"Metric-{index}"
        expected_value = fake.word()
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
    expected_values = [fake.word(), fake.word()]
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


def assert_json_equality(actualJSON, expectedObj):
    actualObj = json.loads(actualJSON)
    print("Expected: ", expectedObj)
    print("Actual: ", actualObj)
    assert actualObj == expectedObj
