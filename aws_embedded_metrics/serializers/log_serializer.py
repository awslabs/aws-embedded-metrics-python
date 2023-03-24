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

from aws_embedded_metrics.config import get_config
from aws_embedded_metrics.logger.metrics_context import MetricsContext
from aws_embedded_metrics.serializers import Serializer
from aws_embedded_metrics.constants import (
    MAX_DIMENSION_SET_SIZE, MAX_METRICS_PER_EVENT, MAX_DATAPOINTS_PER_METRIC
)
from aws_embedded_metrics.exceptions import DimensionSetExceededError
from aws_embedded_metrics.storage_resolution import StorageResolution
import json
from typing import Any, Dict, List


class LogSerializer(Serializer):
    @staticmethod
    def serialize(context: MetricsContext) -> List[str]:
        config = get_config()

        dimension_keys = []
        dimensions_properties: Dict[str, str] = {}

        for dimension_set in context.get_dimensions():
            keys = list(dimension_set.keys())
            if len(keys) > MAX_DIMENSION_SET_SIZE:
                err_msg = (f"Maximum number of dimensions per dimension set allowed are {MAX_DIMENSION_SET_SIZE}. "
                           f"Account for default dimensions if not using set_dimensions.")
                raise DimensionSetExceededError(err_msg)
            dimension_keys.append(keys)
            dimensions_properties = {**dimensions_properties, **dimension_set}

        def create_body() -> Dict[str, Any]:
            body: Dict[str, Any] = {
                **dimensions_properties,
                **context.properties,
            }
            if not config.disable_metric_extraction:
                body["_aws"] = {
                    **context.meta,
                    "CloudWatchMetrics": [
                        {
                            "Dimensions": dimension_keys,
                            "Metrics": [],
                            "Namespace": context.namespace,
                        },
                    ],
                }
            return body

        current_body: Dict[str, Any] = {}
        event_batches: List[str] = []
        num_metrics_in_current_body = 0

        # Track if any given metric has data remaining to be serialized
        remaining_data = True

        # Track batch number to know where to slice metric data
        i = 0
        complete_metrics = set()
        while remaining_data:
            remaining_data = False
            current_body = create_body()

            for metric_name, metric in context.metrics.items():
                # ensure we don't add duplicates of metrics we already completed
                if metric_name in complete_metrics:
                    continue

                if len(metric.values) == 1:
                    current_body[metric_name] = metric.values[0]
                    complete_metrics.add(metric_name)
                else:
                    # Slice metric data as each batch cannot contain more than
                    # MAX_DATAPOINTS_PER_METRIC entries for a given metric
                    start_index = i * MAX_DATAPOINTS_PER_METRIC
                    end_index = (i + 1) * MAX_DATAPOINTS_PER_METRIC
                    current_body[metric_name] = metric.values[start_index:end_index]

                    # Make sure to consume remaining values if we sliced before the end
                    # of the metric value list
                    if len(metric.values) > end_index:
                        remaining_data = True
                    else:
                        complete_metrics.add(metric_name)

                metric_body = {"Name": metric_name, "Unit": metric.unit}
                if metric.storage_resolution == StorageResolution.HIGH:
                    metric_body["StorageResolution"] = metric.storage_resolution.value  # type: ignore
                if not config.disable_metric_extraction:
                    current_body["_aws"]["CloudWatchMetrics"][0]["Metrics"].append(metric_body)
                num_metrics_in_current_body += 1

                if (num_metrics_in_current_body == MAX_METRICS_PER_EVENT):
                    event_batches.append(json.dumps(current_body))
                    current_body = create_body()
                    num_metrics_in_current_body = 0

            # iter over missing datapoints
            i += 1
            if not event_batches or num_metrics_in_current_body > 0:
                event_batches.append(json.dumps(current_body))

        return event_batches
