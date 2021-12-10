# Copyright 2019 Amazon.com, Inc. or its affiliates.
# Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from aws_embedded_metrics import config
from aws_embedded_metrics.environment import Environment
from typing import Generator, Optional

log = logging.getLogger(__name__)

Config = config.get_config()


class EnvironmentCache:
    environment: Optional[Environment] = None


async def resolve_environment() -> Environment:
    if EnvironmentCache.environment is not None:
        log.debug("Environment resolved from cache.")
        return EnvironmentCache.environment

    if Config.environment:
        lower_configured_enviroment = Config.environment.lower()
        if lower_configured_enviroment == "lambda":
            EnvironmentCache.environment = __create_lambda_environment()
        elif lower_configured_enviroment == "ec2":
            EnvironmentCache.environment = __create_ec2_environment()
        elif lower_configured_enviroment == "default":
            EnvironmentCache.environment = __create_default_environment()
        elif lower_configured_enviroment == "local":
            EnvironmentCache.environment = __create_local_environment()
        else:
            log.info("Failed to understand environment override: %s", Config.environment)
    if EnvironmentCache.environment is not None:
        return EnvironmentCache.environment

    for env_under_test in __envs_to_test():
        is_environment = False
        try:
            log.info("Testing environment: %s", env_under_test.__class__.__name__)
            is_environment = await env_under_test.probe()
        except Exception as e:
            log.error(
                "Failed to detect enironment: %s", env_under_test.__class__.__name__, e
            )
            pass

        if is_environment:
            log.info("Detected environment: %s", env_under_test.__class__.__name__)
            EnvironmentCache.environment = env_under_test
            return env_under_test

    log.info("No environment was detected. Using default.")
    EnvironmentCache.environment = __create_default_environment()
    return EnvironmentCache.environment


def __create_lambda_environment() -> Environment:
    from aws_embedded_metrics.environment.lambda_environment import LambdaEnvironment
    return LambdaEnvironment()


def __create_ec2_environment() -> Environment:
    from aws_embedded_metrics.environment.ec2_environment import EC2Environment
    return EC2Environment()


def __create_default_environment() -> Environment:
    from aws_embedded_metrics.environment.default_environment import DefaultEnvironment
    return DefaultEnvironment()


def __create_local_environment() -> Environment:
    from aws_embedded_metrics.environment.local_environment import LocalEnvironment
    return LocalEnvironment()


def __envs_to_test() -> Generator[Environment, None, None]:
    yield __create_lambda_environment()
    yield __create_ec2_environment()
