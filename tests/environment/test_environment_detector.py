from faker import Faker
import os
import pytest
from importlib import reload

from aws_embedded_metrics import config
from aws_embedded_metrics.environment.lambda_environment import LambdaEnvironment
from aws_embedded_metrics.environment.default_environment import DefaultEnvironment

from aws_embedded_metrics.environment import ec2_environment
from aws_embedded_metrics.environment import environment_detector

fake = Faker()


@pytest.fixture
def before():
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = ""

    # reload monkey-patched environments
    reload(ec2_environment)

    # reload detector to reset the cache
    reload(environment_detector)


@pytest.mark.asyncio
async def test_resolve_environment_returns_lambda_environment(before):
    # arrange
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = fake.word()

    # act
    result = await environment_detector.resolve_environment()

    # assert
    assert isinstance(result, LambdaEnvironment)


@pytest.mark.asyncio
async def test_resolve_environment_returns_ec2_envionment(before):
    # arrange
    async def ec2_probe(self):
        return True

    ec2_environment.EC2Environment.probe = ec2_probe

    # act
    result = await environment_detector.resolve_environment()

    # assert
    assert isinstance(result, ec2_environment.EC2Environment)


@pytest.mark.asyncio
async def test_resolve_environment_returns_default_envionment(before):
    # arrange
    # act
    result = await environment_detector.resolve_environment()

    # assert
    assert isinstance(result, DefaultEnvironment)


@pytest.mark.asyncio
async def test_resolve_environment_returns_override_ec2(before, monkeypatch):
    # arrange
    monkeypatch.setenv("AWS_EMF_ENVIRONMENT", "ec2")
    reload(config)
    reload(environment_detector)

    # act
    result = await environment_detector.resolve_environment()

    # assert
    assert isinstance(result, ec2_environment.EC2Environment)


@pytest.mark.asyncio
async def test_resolve_environment_returns_override_lambda(before, monkeypatch):
    # arrange
    monkeypatch.setenv("AWS_EMF_ENVIRONMENT", "lambda")
    reload(config)
    reload(environment_detector)

    # act
    result = await environment_detector.resolve_environment()

    # assert
    assert isinstance(result, LambdaEnvironment)
