from aws_embedded_metrics import config
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics import utils
from aws_embedded_metrics.constants import DEFAULT_NAMESPACE
from _pytest.monkeypatch import MonkeyPatch
import pytest
from importlib import reload
from faker import Faker

fake = Faker()


@pytest.fixture
def mock_time():
    expected_time = fake.random.randrange(0, 1000)
    monkeypatch = MonkeyPatch()
    monkeypatch.setattr(utils, "now", lambda: expected_time)
    return expected_time


def test_can_create_context_with_no_arguments(mock_time):
    # reload the configuration module since it is loaded on
    # startup and cached
    reload(config)

    # arrange
    # act
    context = MetricsContext()

    # assert
    assert context.namespace == DEFAULT_NAMESPACE
    assert context.meta == {"Timestamp": mock_time}
    assert context.properties == {}
    assert context.dimensions == []
    assert context.default_dimensions == {}


def test_can_set_property(mock_time):
    # arrange
    context = MetricsContext()

    property_key = fake.word()
    property_value = fake.word()

    # act
    context.properties[property_key] = property_value

    # assert
    assert context.properties == {property_key: property_value}


def test_put_dimension_adds_to_dimensions(mock_time):
    # arrange
    context = MetricsContext()

    dimension_key = fake.word()
    dimension_value = fake.word()

    # act
    context.put_dimensions({dimension_key: dimension_value})

    # assert
    assert context.dimensions == [{dimension_key: dimension_value}]


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


def test_put_metric_adds_metrics():
    # arrange
    context = MetricsContext()
    metric_key = fake.word()
    metric_value = fake.random.random()
    metric_unit = fake.word()

    # act
    context.put_metric(metric_key, metric_value, metric_unit)

    # assert
    metric = context.metrics[metric_key]
    assert metric.unit == metric_unit
    assert metric.values == [metric_value]


def test_put_metric_uses_None_unit_if_not_provided():
    # arrange
    context = MetricsContext()
    metric_key = fake.word()
    metric_value = fake.random.random()

    # act
    context.put_metric(metric_key, metric_value)

    # assert
    metric = context.metrics[metric_key]
    assert metric.unit == "None"


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
    context.set_default_dimensions({fake.word(): fake.word})
    context.put_dimensions({fake.word(): fake.word})

    expected_dimensions = {fake.word(): fake.word}

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
