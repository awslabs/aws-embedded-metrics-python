from aws_embedded_metrics.config import get_config
from aws_embedded_metrics import metric_scope
import pytest
import boto3
import logging
import os
import asyncio
from datetime import datetime, timedelta

# enable verbose logging in case something goes wrong
# pytest won't actually output any of the logs unless it fails
logging.basicConfig(level=logging.INFO)
client = boto3.client("cloudwatch", region_name=os.environ["AWS_REGION"])

Config = get_config()
Config.service_name = "IntegrationTests"
Config.service_type = "AutomatedTest"
Config.log_group_name = "aws-emf-python-integ"

start_time = datetime.utcnow()


@pytest.mark.timeout(120)
@pytest.mark.asyncio
async def test_end_to_end_tcp_multiple_flushes():
    # arrange
    # ensure we don't incorrectly detect as Lambda environment
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = ""
    Config.agent_endpoint = "tcp://0.0.0.0:25888"

    metric_name = "TCP-MultiFlush"
    expected_sample_count = 3

    @metric_scope
    async def do_work(metrics):
        metrics.put_dimensions({"Operation": "Agent"})
        metrics.put_metric(metric_name, 100, "Milliseconds")
        metrics.set_property("RequestId", "422b1569-16f6-4a03-b8f0-fe3fd9b100f8")

    # act
    await do_work()
    await do_work()
    await asyncio.sleep(5)
    await do_work()

    # assert
    attempts = 0
    while metric_exists(metric_name, expected_sample_count) is False:
        attempts += 1
        print(f"No metrics yet. Sleeping before trying again. Attempt # {attempts}")
        await asyncio.sleep(expected_sample_count)


@pytest.mark.timeout(120)
@pytest.mark.asyncio
async def test_end_to_end_udp():
    # arrange
    # ensure we don't incorrectly detect as Lambda environment
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = ""
    Config.agent_endpoint = "udp://0.0.0.0:25888"

    metric_name = "UDP-SingleFlush"

    @metric_scope
    async def do_work(metrics):
        metrics.put_dimensions({"Operation": "Agent"})
        metrics.put_metric(metric_name, 100, "Milliseconds")
        metrics.set_property("RequestId", "422b1569-16f6-4a03-b8f0-fe3fd9b100f8")

    # act
    await do_work()

    # assert
    attempts = 0
    while metric_exists(metric_name) is False:
        attempts += 1
        print(f"No metrics yet. Sleeping before trying again. Attempt # {attempts}")
        await asyncio.sleep(2)


def metric_exists(metric_name, expected_samples=1):
    response = client.get_metric_statistics(
        Namespace="aws-embedded-metrics",
        MetricName=metric_name,
        Dimensions=[
            {"Name": "ServiceName", "Value": Config.service_name},
            {"Name": "ServiceType", "Value": Config.service_type},
            {"Name": "LogGroup", "Value": Config.log_group_name},
            {"Name": "Operation", "Value": "Agent"},
        ],
        StartTime=start_time - timedelta(seconds=1),
        EndTime=datetime.utcnow(),
        Period=60,
        Statistics=["SampleCount", "Average"],
        Unit="Milliseconds",
    )

    if len(response["Datapoints"]) > 0:
        sample_count = response["Datapoints"][0]["SampleCount"]
        if sample_count == expected_samples:
            return True
        else:
            print(response["Datapoints"])

    return False
