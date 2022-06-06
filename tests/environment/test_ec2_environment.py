from aws_embedded_metrics.config import get_config

from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.environment.ec2_environment import EC2Environment
import pytest
import json
from faker import Faker
from faker.providers import internet


fake = Faker()
fake.add_provider(internet)
Config = get_config()


@pytest.mark.asyncio
async def test_probe_returns_true_if_fetch_succeeds(aresponses):
    # arrange
    configure_response(aresponses, fake.pystr(), "{}")
    env = EC2Environment()

    # act
    result = await env.probe()

    # assert
    assert result is True


def test_get_name_returns_unknown_if_not_configured():
    # arrange
    Config.service_name = ""
    env = EC2Environment()

    # act
    result = env.get_name()

    # assert
    assert result == "Unknown"


def test_get_name_returns_configured_name():
    # arrange
    expected = fake.word()
    Config.service_name = expected
    env = EC2Environment()

    # act
    result = env.get_name()

    # assert
    assert result == expected


@pytest.mark.asyncio
async def test_get_type_returns_ec2_instance(aresponses):
    # arrange
    expected = "AWS::EC2::Instance"
    configure_response(aresponses, fake.pystr(), "{}")
    env = EC2Environment()

    # environment MUST be detected before we can access the metadata
    await env.probe()

    # act
    result = env.get_type()

    # assert
    assert result == expected


@pytest.mark.asyncio
async def test_configure_context_adds_ec2_metadata_props(aresponses):
    # arrange
    image_id = fake.word()
    instance_id = fake.word()
    instance_type = fake.word()
    private_ip = fake.ipv4()
    az = fake.word()

    configure_response(
        aresponses,
        fake.pystr(),
        json.dumps(
            {
                "imageId": image_id,
                "instanceId": instance_id,
                "instanceType": instance_type,
                "privateIp": private_ip,
                "availabilityZone": az,
            }
        ),
    )
    env = EC2Environment()
    context = MetricsContext.empty()

    # environment MUST be detected before we can access the metadata
    await env.probe()

    # act
    env.configure_context(context)

    # assert
    assert context.properties["imageId"] == image_id
    assert context.properties["instanceId"] == instance_id
    assert context.properties["instanceType"] == instance_type
    assert context.properties["privateIp"] == private_ip
    assert context.properties["availabilityZone"] == az


# Test helper methods


def configure_response(aresponses, token, json):
    aresponses.add(
        "169.254.169.254",
        "/latest/api/token",
        "put",
        aresponses.Response(text=token, headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}),
    )
    aresponses.add(
        "169.254.169.254",
        "/latest/dynamic/instance-identity/document",
        "get",
        # the ec2-metdata endpoint does not actually set the correct
        # content-type header, it will instead use text/plain
        aresponses.Response(text=json,
                            content_type="text/plain",
                            headers={"X-aws-ec2-metadata-token": token})
    )
