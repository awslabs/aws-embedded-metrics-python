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
from aws_embedded_metrics.constants import MAX_DIMENSIONS, MAX_METRICS_PER_EVENT
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
            dimension_keys.append(keys[0:MAX_DIMENSIONS])
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

        current_body: Dict[str, Any] = create_body()
        event_batches: List[str] = []
        num_metrics_in_current_body = 0

        for metric_name, metric in context.metrics.items():

            if len(metric.values) == 1:
                current_body[metric_name] = metric.values[0]
            else:
                current_body[metric_name] = metric.values

            if not config.disable_metric_extraction:
                current_body["_aws"]["CloudWatchMetrics"][0]["Metrics"].append({"Name": metric_name, "Unit": metric.unit})

            num_metrics_in_current_body += 1

            should_serialize: bool = num_metrics_in_current_body == MAX_METRICS_PER_EVENT
            if should_serialize:
                event_batches.append(json.dumps(current_body))
                current_body = create_body()
                num_metrics_in_current_body = 0

        if not event_batches or num_metrics_in_current_body > 0:
            event_batches.append(json.dumps(current_body))

        return event_batches
