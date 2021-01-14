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
from aws_embedded_metrics.environment.default_environment import DefaultEnvironment
from aws_embedded_metrics.environment.lambda_environment import LambdaEnvironment
from aws_embedded_metrics.environment.local_environment import LocalEnvironment
from aws_embedded_metrics.environment.ec2_environment import EC2Environment
from typing import Optional

log = logging.getLogger(__name__)

lambda_environment = LambdaEnvironment()
ec2_environment = EC2Environment()
default_environment = DefaultEnvironment()
local_environment = LocalEnvironment()
environments = [lambda_environment, ec2_environment]
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
            EnvironmentCache.environment = lambda_environment
        elif lower_configured_enviroment == "ec2":
            EnvironmentCache.environment = ec2_environment
        elif lower_configured_enviroment == "default":
            EnvironmentCache.environment = default_environment
        elif lower_configured_enviroment == "local":
            EnvironmentCache.environment = local_environment
        else:
            log.info("Failed to understand environment override: %s", Config.environment)
    if EnvironmentCache.environment is not None:
        return EnvironmentCache.environment

    for env_under_test in environments:
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
    EnvironmentCache.environment = default_environment
    return EnvironmentCache.environment
