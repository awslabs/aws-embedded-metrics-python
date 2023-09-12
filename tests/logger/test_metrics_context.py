from faker import Faker
from importlib import reload
from datetime import datetime
import pytest
import math
import random
from aws_embedded_metrics import constants, utils
from aws_embedded_metrics.unit import Unit
from aws_embedded_metrics.storage_resolution import StorageResolution
from aws_embedded_metrics import config
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.constants import DEFAULT_NAMESPACE, MAX_TIMESTAMP_FUTURE_AGE, MAX_TIMESTAMP_PAST_AGE
from aws_embedded_metrics.exceptions import DimensionSetExceededError, InvalidDimensionError, InvalidMetricError
from aws_embedded_metrics.exceptions import InvalidTimestampError

fake = Faker()


def test_can_create_context_with_no_arguments():
    # reload the configuration module since it is loaded on
    # startup and cached
    reload(config)

    # arrange
    # act
    context = MetricsContext()

    # assert
    assert context.namespace == DEFAULT_NAMESPACE
    assert context.meta["Timestamp"] > 0
    assert context.properties == {}
    assert context.dimensions == []
    assert context.default_dimensions == {}


def test_can_set_property():
    # arrange
    context = MetricsContext()

    property_key = fake.word()
    property_value = fake.word()

    # act
    context.properties[property_key] = property_value

    # assert
    assert context.properties == {property_key: property_value}


def test_put_dimension_adds_to_dimensions():
    # arrange
    context = MetricsContext()

    dimensions_to_add = 30
    dimension_set = generate_dimension_set(dimensions_to_add)

    # act
    context.put_dimensions(dimension_set)

    # assert
    assert context.dimensions == [dimension_set]


def test_put_dimensions_accept_multiple_unique_dimensions():
    # arrange
    context = MetricsContext()
    dimension1 = {fake.word(): fake.word()}
    dimension2 = {fake.word(): fake.word()}

    # act
    context.put_dimensions(dimension1)
    context.put_dimensions(dimension2)

    # assert
    assert len(context.get_dimensions()) == 2
    assert context.get_dimensions()[0] == dimension1
    assert context.get_dimensions()[1] == dimension2


def test_put_dimensions_prevent_duplicate_dimensions():
    # arrange
    context = MetricsContext()
    pair1 = [fake.word(), fake.word()]
    pair2 = [fake.word(), fake.word()]

    dimension1 = {pair1[0]: pair1[1]}
    dimension2 = {pair2[0]: pair2[1]}
    dimension3 = {pair1[0]: pair1[1], pair2[0]: pair2[1]}

    # act
    context.put_dimensions(dimension1)
    context.put_dimensions(dimension2)
    context.put_dimensions(dimension1)
    context.put_dimensions(dimension3)
    context.put_dimensions(dimension2)
    context.put_dimensions(dimension3)

    # assert
    assert len(context.get_dimensions()) == 3
    assert context.get_dimensions()[0] == dimension1
    assert context.get_dimensions()[1] == dimension2
    assert context.get_dimensions()[2] == dimension3


def test_put_dimensions_use_most_recent_dimension_value():
    # arrange
    context = MetricsContext()
    key1 = fake.word()
    key2 = fake.word()
    val1 = fake.word()
    val2 = fake.word()

    dimension1 = {key1: val1}
    dimension2 = {key2: val2}
    dimension3 = {key1: val2}
    dimension4 = {key2: val1}
    dimension5 = {key1: val1, key2: val2}
    dimension6 = {key1: val2, key2: val1}

    # act
    context.put_dimensions(dimension1)
    context.put_dimensions(dimension2)
    context.put_dimensions(dimension5)
    context.put_dimensions(dimension3)
    context.put_dimensions(dimension4)
    context.put_dimensions(dimension6)

    # assert
    assert len(context.get_dimensions()) == 3
    assert context.get_dimensions()[0] == dimension3
    assert context.get_dimensions()[1] == dimension4
    assert context.get_dimensions()[2] == dimension6


def test_put_dimensions_with_set_dimensions():
    # arrange
    context = MetricsContext()
    key1 = fake.word()
    key2 = fake.word()
    val1 = fake.word()
    val2 = fake.word()

    dimension1 = {key1: val1}
    dimension2 = {key2: val2}
    dimension3 = {key1: val2}
    dimension4 = {key2: val1}
    dimension5 = {key1: val1, key2: val2}
    dimension6 = {key1: val2, key2: val1}

    # act
    context.put_dimensions(dimension1)
    context.put_dimensions(dimension2)
    context.set_dimensions([dimension3])
    context.put_dimensions(dimension4)
    context.put_dimensions(dimension5)
    context.put_dimensions(dimension6)

    # assert
    assert len(context.get_dimensions()) == 3
    assert context.get_dimensions()[0] == dimension3
    assert context.get_dimensions()[1] == dimension4
    assert context.get_dimensions()[2] == dimension6


def test_get_dimensions_returns_only_custom_dimensions_if_no_default_dimensions_not_set():
    # arrange
    context = MetricsContext()
    dimension_key = fake.word()
    dimension_value = fake.word()
    expected_dimensions = {dimension_key: dimension_value}

    context.set_default_dimensions(None)
    context.put_dimensions(expected_dimensions)

    # act
    actual_dimensions = context.get_dimensions()

    # assert
    assert [expected_dimensions] == actual_dimensions


def test_get_dimensions_returns_only_custom_dimensions_if_default_dimensions_are_empty():
    # arrange
    context = MetricsContext()
    dimension_key = fake.word()
    dimension_value = fake.word()
    expected_dimensions = {dimension_key: dimension_value}

    context.set_default_dimensions({})
    context.put_dimensions(expected_dimensions)

    # act
    actual_dimensions = context.get_dimensions()

    # assert
    assert [expected_dimensions] == actual_dimensions


def test_get_dimensions_returns_default_dimensions_if_custom_dimensions_not_set():
    # arrange
    context = MetricsContext()
    dimension_key = fake.word()
    dimension_value = fake.word()
    expected_dimensions = {dimension_key: dimension_value}
    context.set_default_dimensions(expected_dimensions)

    # act
    actual_dimensions = context.get_dimensions()

    # assert
    assert [expected_dimensions] == actual_dimensions


def test_get_dimensions_returns_merged_custom_and_default_dimensions():
    # arrange
    context = MetricsContext()
    custom_dimension_key = fake.word()
    custom_dimension_value = fake.word()

    default_dimension_key = fake.word()
    default_dimension_value = fake.word()

    expected_dimensions = {
        default_dimension_key: default_dimension_value,
        custom_dimension_key: custom_dimension_value,
    }

    context.set_default_dimensions({default_dimension_key: default_dimension_value})
    context.put_dimensions({custom_dimension_key: custom_dimension_value})

    # act
    actual_dimensions = context.get_dimensions()

    # assert
    assert [expected_dimensions] == actual_dimensions


@pytest.mark.parametrize(
    "name, value",
    [
        (None, "value"),
        ("", "value"),
        (" ", "value"),
        ("a" * (constants.MAX_DIMENSION_NAME_LENGTH + 1), "value"),
        ("ḓɨɱɛɳʂɨøɳ", "value"),
        (":dim", "value"),
        ("dim", ""),
        ("dim", " "),
        ("dim", "a" * (constants.MAX_DIMENSION_VALUE_LENGTH + 1)),
        ("dim", "ṽɑɭʊɛ"),
    ]
)
def test_add_invalid_dimensions_raises_exception(name, value):
    context = MetricsContext()

    with pytest.raises(InvalidDimensionError):
        context.put_dimensions({name: value})

    with pytest.raises(InvalidDimensionError):
        context.set_dimensions([{name: value}])


def test_put_metric_adds_metrics():
    # arrange
    context = MetricsContext()
    metric_key = fake.word()
    metric_value = fake.random.random()
    metric_unit = random.choice(list(Unit)).value
    metric_storage_resolution = random.choice(list(StorageResolution)).value

    # act
    context.put_metric(metric_key, metric_value, metric_unit, metric_storage_resolution)

    # assert
    metric = context.metrics[metric_key]
    assert metric.unit == metric_unit
    assert metric.values == [metric_value]
    assert metric.storage_resolution == metric_storage_resolution


def test_put_metric_uses_none_unit_if_not_provided():
    # arrange
    context = MetricsContext()
    metric_key = fake.word()
    metric_value = fake.random.random()

    # act
    context.put_metric(metric_key, metric_value)

    # assert
    metric = context.metrics[metric_key]
    assert metric.unit == "None"


def test_put_metric_uses_standard_storage_resolution_if_not_provided():
    # arrange
    context = MetricsContext()
    metric_key = fake.word()
    metric_value = fake.random.random()

    # act
    context.put_metric(metric_key, metric_value)

    # assert
    metric = context.metrics[metric_key]
    assert metric.storage_resolution == StorageResolution.STANDARD


@pytest.mark.parametrize(
    "name, value, unit, storage_resolution",
    [
        ("", 1, "None", StorageResolution.STANDARD),
        (" ", 1, "Seconds", StorageResolution.STANDARD),
        ("a" * (constants.MAX_METRIC_NAME_LENGTH + 1), 1, "None", StorageResolution.STANDARD),
        ("metric", float("inf"), "Count", StorageResolution.STANDARD),
        ("metric", float("-inf"), "Count", StorageResolution.STANDARD),
        ("metric", float("nan"), "Count", StorageResolution.STANDARD),
        ("metric", math.inf, "Seconds", StorageResolution.STANDARD),
        ("metric", -math.inf, "Seconds", StorageResolution.STANDARD),
        ("metric", math.nan, "Seconds", StorageResolution.STANDARD),
        ("metric", 1, "Kilometers/Fahrenheit", StorageResolution.STANDARD),
        ("metric", 1, "Seconds", 2),
        ("metric", 1, "Seconds", 0),
        ("metric", 1, "Seconds", None)
    ]
)
def test_put_invalid_metric_raises_exception(name, value, unit, storage_resolution):
    context = MetricsContext()

    with pytest.raises(InvalidMetricError):
        context.put_metric(name, value, unit, storage_resolution)


def test_create_copy_with_context_creates_new_instance():
    # arrange
    context = MetricsContext()

    # act
    new_context = context.create_copy_with_context()

    # assert
    assert new_context is not context


def test_create_copy_with_context_copies_namespace():
    # arrange
    context = MetricsContext()
    context.namespace = fake.word()

    # act
    new_context = context.create_copy_with_context()

    # assert
    assert context.namespace == new_context.namespace


def test_create_copy_with_context_copies_properties():
    # arrange
    context = MetricsContext()
    prop_key = fake.word()
    prop_value = fake.word()
    context.set_property(prop_key, prop_value)

    # act
    new_context = context.create_copy_with_context()

    # assert
    assert context.properties == new_context.properties
    assert context.properties is not new_context.properties


def test_create_copy_with_context_does_not_copy_dimensions():
    # arrange
    context = MetricsContext()
    dimension_key = fake.word()
    dimension_value = fake.word()
    context.put_dimensions({dimension_key: dimension_value})

    # act
    new_context = context.create_copy_with_context()

    # assert
    assert len(new_context.dimensions) == 0


def test_create_copy_with_context_copies_default_dimensions():
    # arrange
    context = MetricsContext()
    context.set_default_dimensions({fake.word(): fake.word})

    # act
    new_context = context.create_copy_with_context()

    # assert
    assert context.default_dimensions == new_context.default_dimensions
    assert context.default_dimensions is not new_context.default_dimensions


def test_create_copy_with_context_does_not_copy_metrics():
    # arrange
    context = MetricsContext()
    prop_key = fake.word()
    prop_value = fake.word()
    context.set_property(prop_key, prop_value)

    # act
    new_context = context.create_copy_with_context()

    # assert
    assert len(new_context.metrics) == 0


def test_set_dimensions_overwrites_all_dimensions():
    # arrange
    context = MetricsContext()
    context.set_default_dimensions({fake.word(): fake.word()})
    context.put_dimensions({fake.word(): fake.word()})

    expected_dimensions = [{fake.word(): fake.word()}]

    # act
    context.set_dimensions(expected_dimensions)

    # assert
    assert context.dimensions == expected_dimensions


def test_create_copy_with_context_does_not_repeat_dimensions():
    # arrange
    context = MetricsContext()
    expected_dimensions = {fake.word(): fake.word()}

    custom = {fake.word(): fake.word()}
    context.set_default_dimensions(expected_dimensions)
    context.put_dimensions(custom)

    new_context = context.create_copy_with_context()
    new_context.set_default_dimensions(expected_dimensions)
    new_context.put_dimensions(custom)

    # assert
    assert len(new_context.get_dimensions()) == 1


def test_cannot_set_more_than_30_dimensions():
    context = MetricsContext()
    dimensions_to_add = 32
    dimension_set = generate_dimension_set(dimensions_to_add)

    with pytest.raises(DimensionSetExceededError):
        context.set_dimensions([dimension_set])


def test_cannot_put_more_than_30_dimensions():
    context = MetricsContext()
    dimensions_to_add = 32
    dimension_set = generate_dimension_set(dimensions_to_add)

    with pytest.raises(DimensionSetExceededError):
        context.put_dimensions(dimension_set)


@pytest.mark.parametrize(
    "timestamp",
    [
        datetime.datetime.now(),
        datetime.datetime.now() - datetime.timedelta(milliseconds=MAX_TIMESTAMP_PAST_AGE - 5000),
        datetime.datetime.now() + datetime.timedelta(milliseconds=MAX_TIMESTAMP_FUTURE_AGE - 5000)
    ]
)
def test_set_timestamp_sets_timestamp(timestamp: datetime.datetime):
    context = MetricsContext()

    context.set_timestamp(timestamp)

    assert context.meta[constants.TIMESTAMP] == utils.convert_to_milliseconds(timestamp)


@pytest.mark.parametrize(
    "timestamp",
    [
        None,
        datetime.datetime.min,
        datetime.datetime.max,
        datetime.datetime(1, 1, 1, 0, 0, 0, 0, None),
        datetime.datetime(1, 1, 1),
        datetime.datetime(1, 1, 1, 0, 0),
        datetime.datetime(9999, 12, 31, 23, 59, 59, 999999),
        datetime.datetime.now() - datetime.timedelta(milliseconds=MAX_TIMESTAMP_PAST_AGE + 5000),
        datetime.datetime.now() + datetime.timedelta(milliseconds=MAX_TIMESTAMP_FUTURE_AGE + 5000)
    ]
)
def test_set_invalid_timestamp_raises_exception(timestamp: datetime):
    context = MetricsContext()

    with pytest.raises(InvalidTimestampError):
        context.set_timestamp(timestamp)


# Test utility method


def generate_dimension_set(dimensions_to_add):
    dimension_set = {}
    for i in range(0, dimensions_to_add):
        dimension_set[f"{i}"] = fake.word()

    return dimension_set
