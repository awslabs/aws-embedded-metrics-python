from aws_embedded_metrics.sinks.lambda_sink import LambdaSink
from aws_embedded_metrics.logger.metrics_context import MetricsContext


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
