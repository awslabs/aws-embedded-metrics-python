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
    expected["CloudWatchMetrics"][0]["Dimensions"].append([expected_key])

    context = get_context()
    context.put_dimensions(dimensions)

    # act
    result_json = serializer.serialize(context)

    # assert
    assert_json_equality(result_json, expected)


def test_cannot_serialize_more_than_10_dimensions():
    # arrange
    dimensions = {}
    dimension_pointers = []
    allowed_dimensions = 10
    dimensions_to_add = 15

    for i in range(0, dimensions_to_add):
        print(i)
        expected_key = f"{i}"
        expected_value = fake.word()
        dimensions[expected_key] = expected_value
        dimension_pointers.append(expected_key)

    expected_dimensions_pointers = dimension_pointers[0:allowed_dimensions]

    expected = {**get_empty_payload(), **dimensions}
    expected["CloudWatchMetrics"][0]["Dimensions"].append(expected_dimensions_pointers)

    context = get_context()
    context.put_dimensions(dimensions)

    # act
    result_json = serializer.serialize(context)

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
    result_json = serializer.serialize(context)

    # assert
    assert_json_equality(result_json, expected)


def test_serialize_metrics():
    # arrange
    expected_key = fake.word()
    expected_value = fake.random.randrange(0, 100)

    expected_metric_definition = {"Name": expected_key, "Unit": "None"}

    expected = {**get_empty_payload()}
    expected[expected_key] = expected_value
    expected["CloudWatchMetrics"][0]["Metrics"].append(expected_metric_definition)

    context = get_context()
    context.put_metric(expected_key, expected_value)

    # act
    result_json = serializer.serialize(context)

    # assert
    assert_json_equality(result_json, expected)


# Test utility method


def get_context():
    context = MetricsContext.empty()
    context.set_property("Timestamp", 0)
    return context


def get_empty_payload():
    return {
        "CloudWatchMetrics": [
            {"Dimensions": [], "Metrics": [], "Namespace": "aws-embedded-metrics"}
        ],
        "Version": "0",
        "Timestamp": 0,
    }


def assert_json_equality(actualJSON, expectedObj):
    actualObj = json.loads(actualJSON)
    print("Expected: ", expectedObj)
    print("Actual: ", actualObj)
    assert actualObj == expectedObj
