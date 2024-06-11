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

from aws_embedded_metrics.logger.metrics_logger_factory import create_metrics_logger
import inspect
import asyncio
from functools import wraps


def metric_scope(fn):  # type: ignore
    if inspect.isasyncgenfunction(fn):
        @wraps(fn)
        async def async_gen_wrapper(*args, **kwargs):  # type: ignore
            logger = create_metrics_logger()
            if "metrics" in inspect.signature(fn).parameters:
                kwargs["metrics"] = logger

            try:
                fn_gen = fn(*args, **kwargs)
                while True:
                    result = await fn_gen.__anext__()
                    await logger.flush()
                    yield result
            except Exception as ex:
                await logger.flush()
                if not isinstance(ex, StopIteration):
                    raise

        return async_gen_wrapper

    elif inspect.isgeneratorfunction(fn):
        @wraps(fn)
        def gen_wrapper(*args, **kwargs):  # type: ignore
            logger = create_metrics_logger()
            if "metrics" in inspect.signature(fn).parameters:
                kwargs["metrics"] = logger

            try:
                fn_gen = fn(*args, **kwargs)
                while True:
                    result = next(fn_gen)
                    asyncio.run(logger.flush())
                    yield result
            except Exception as ex:
                asyncio.run(logger.flush())
                if not isinstance(ex, StopIteration):
                    raise

        return gen_wrapper

    elif asyncio.iscoroutinefunction(fn):
        @wraps(fn)
        async def async_wrapper(*args, **kwargs):  # type: ignore
            logger = create_metrics_logger()
            if "metrics" in inspect.signature(fn).parameters:
                kwargs["metrics"] = logger

            try:
                return await fn(*args, **kwargs)
            finally:
                await logger.flush()

        return async_wrapper

    else:
        @wraps(fn)
        def wrapper(*args, **kwargs):  # type: ignore
            logger = create_metrics_logger()
            if "metrics" in inspect.signature(fn).parameters:
                kwargs["metrics"] = logger

            try:
                return fn(*args, **kwargs)
            finally:
                asyncio.run(logger.flush())

        return wrapper
