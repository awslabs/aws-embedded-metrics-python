from aws_embedded_metrics.sinks.lambda_sink import LambdaSink
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from faker import Faker
from unittest.mock import patch


fake = Faker()


def test_accept_writes_to_stdout(capfd):
    # arrange
    sink = LambdaSink()
    context = MetricsContext.empty()
    context.meta["Timestamp"] = 1

    # act
    sink.accept(context)

    # assert
    out, err = capfd.readouterr()
    assert (
        out
        == '{"_aws": {"Timestamp": 1, "CloudWatchMetrics": [{"Dimensions": [], "Metrics": [], "Namespace": "aws-embedded-metrics"}]}}\n'
    )


@patch("aws_embedded_metrics.serializers.log_serializer.LogSerializer")
def test_accept_writes_multiple_messages_to_stdout(mock_serializer, capfd):
    # arrange
    expected_messages = [fake.word() for _ in range(10)]
    mock_serializer.serialize.return_value = expected_messages
    sink = LambdaSink(serializer=mock_serializer)
    context = MetricsContext.empty()
    context.meta["Timestamp"] = 1

    # act
    sink.accept(context)

    # assert
    out, err = capfd.readouterr()
    assert len(out.split()) == len(expected_messages)
    assert out.split() == expected_messages
