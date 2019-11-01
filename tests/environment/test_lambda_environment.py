import os
from aws_embedded_metrics.environment.lambda_environment import LambdaEnvironment
from aws_embedded_metrics.sinks.lambda_sink import LambdaSink

from faker import Faker

fake = Faker()


def test_probe_returns_true_if_fcn_name_in_env():
    # arrange
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = fake.word()
    env = LambdaEnvironment()

    # act
    result = env.probe()

    # assert
    assert result is True


def test_get_name_returns_function_name():
    # arrange
    expected_name = fake.word()
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = expected_name
    env = LambdaEnvironment()

    # act
    result = env.get_name()

    # assert
    assert result == expected_name


def test_get_type_returns_cfn_lambda_name():
    # arrange
    env = LambdaEnvironment()

    # act
    result = env.get_type()

    # assert
    assert result == "AWS::Lambda::Function"


def test_get_log_group_name_returns_function_name():
    # arrange
    expected_name = fake.word()
    os.environ["AWS_LAMBDA_FUNCTION_NAME"] = expected_name
    env = LambdaEnvironment()

    # act
    result = env.get_log_group_name()

    # assert
    assert result == expected_name


def test_create_sink_creates_LambdaSink():
    # arrange
    env = LambdaEnvironment()

    # act
    result = env.get_sink()

    # assert
    assert isinstance(result, LambdaSink)
