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

import math
import re
from typing import Dict, Optional
from aws_embedded_metrics.unit import Unit
from aws_embedded_metrics.storage_resolution import StorageResolution
from aws_embedded_metrics.exceptions import DimensionSetExceededError, InvalidDimensionError, InvalidMetricError, InvalidNamespaceError
import aws_embedded_metrics.constants as constants


def validate_dimension_set(dimension_set: Dict[str, str]) -> None:
    """
    Validates a dimension set

        Parameters:
            dimension_set (Dict[str, str]): The dimension set to validate

        Raises:
            DimensionSetExceededError: If the dimension set is too large
            InvalidDimensionError: If a dimension is invalid
    """
    if len(dimension_set) > constants.MAX_DIMENSION_SET_SIZE:
        raise DimensionSetExceededError(
            f"Maximum number of dimensions per dimension set allowed are {constants.MAX_DIMENSION_SET_SIZE}")

    for name, value in dimension_set.items():
        if not name or len(name.strip()) == 0:
            raise InvalidDimensionError("Dimension name must include at least one non-whitespace character")

        if not value or len(value.strip()) == 0:
            raise InvalidDimensionError("Dimension value must include at least one non-whitespace character")

        if len(name) > constants.MAX_DIMENSION_NAME_LENGTH:
            raise InvalidDimensionError(f"Dimension name cannot be longer than {constants.MAX_DIMENSION_NAME_LENGTH} characters")

        if len(value) > constants.MAX_DIMENSION_VALUE_LENGTH:
            raise InvalidDimensionError(f"Dimension value cannot be longer than {constants.MAX_DIMENSION_VALUE_LENGTH} characters")

        if not name.isascii():
            raise InvalidDimensionError(f"Dimension name contains invalid characters: {name}")

        if not value.isascii():
            raise InvalidDimensionError(f"Dimension value contains invalid characters: {value}")

        if name.startswith(":"):
            raise InvalidDimensionError("Dimension name cannot start with ':'")


def validate_metric(name: str,
                    value: float,
                    unit: Optional[str],
                    storage_resolution: StorageResolution,
                    metric_name_and_resolution_map: dict) -> None:
    """
    Validates a metric

        Parameters:
            name (str): The name of the metric
            value (float): The value of the metric
            unit (Optional[str]): The unit of the metric
            storage_resolution (Optional[int]): The storage resolution of metric
            metric_name_and_resolution_map (dict): The map used for validating metric

        Raises:
            InvalidMetricError: If the metric is invalid
    """
    if not name or len(name.strip()) == 0:
        raise InvalidMetricError("Metric name must include at least one non-whitespace character")

    if len(name) > constants.MAX_DIMENSION_NAME_LENGTH:
        raise InvalidMetricError(f"Metric name cannot be longer than {constants.MAX_DIMENSION_NAME_LENGTH} characters")

    if not math.isfinite(value):
        raise InvalidMetricError("Metric value must be finite")

    if unit is not None and unit not in Unit:
        raise InvalidMetricError(f"Metric unit is not valid: {unit}")

    if storage_resolution is None or storage_resolution not in StorageResolution:
        raise InvalidMetricError(f"Metric storage resolution is not valid: {storage_resolution}")

    if name in metric_name_and_resolution_map and metric_name_and_resolution_map.get(name) is not storage_resolution:
        raise InvalidMetricError(
            f"Resolution for metrics {name} is already set. A single log event cannot have a metric with two different resolutions.")


def validate_namespace(namespace: str) -> None:
    """
    Validates a namespace

        Parameters:
            namespace (str): The namespace to validate

        Raises:
            InvalidNamespaceError: If the namespace is invalid
    """
    if not namespace or len(namespace.strip()) == 0:
        raise InvalidNamespaceError("Namespace must include at least one non-whitespace character")

    if len(namespace) > constants.MAX_NAMESPACE_LENGTH:
        raise InvalidNamespaceError(f"Namespace cannot be longer than {constants.MAX_NAMESPACE_LENGTH} characters")

    if not re.match(constants.VALID_NAMESPACE_REGEX, namespace):
        raise InvalidNamespaceError(f"Namespace contains invalid characters: {namespace}")
