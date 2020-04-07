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


from aws_embedded_metrics import constants, utils
from aws_embedded_metrics.config import get_config
from aws_embedded_metrics.logger.metric import Metric
from typing import List, Dict, Any


class MetricsContext(object):
    """
    Stores metrics and their associated properties and dimensions.
    """

    def __init__(
        self,
        namespace: str = None,
        properties: Dict[str, Any] = None,
        dimensions: List[Dict[str, str]] = None,
        default_dimensions: Dict[str, str] = None,
    ):

        self.namespace: str = namespace or get_config().namespace or constants.DEFAULT_NAMESPACE
        self.properties: Dict[str, Any] = properties or {}
        self.dimensions: List[Dict[str, str]] = dimensions or []
        self.default_dimensions: Dict[str, str] = default_dimensions or {}
        self.metrics: Dict[str, Metric] = {}
        self.should_use_default_dimensions = True
        self.meta: Dict[str, Any] = {"Timestamp": utils.now()}

    def put_metric(self, key: str, value: float, unit: str = None) -> None:
        """
        Adds a metric measurement to the context.
        Multiple calls using the same key will be stored as an
        array of scalar values.
        ```
        context.put_metric("Latency", 100, "Milliseconds")
        ```
        """
        metric = self.metrics.get(key)
        if metric:
            # TODO: we should log a warning if the unit has been changed
            metric.add_value(value)
        else:
            self.metrics[key] = Metric(value, unit)

    def put_dimensions(self, dimensions: Dict[str, str]) -> None:
        """
        Adds dimensions to the context.
        ```
        context.put_dimensions({ "k1": "v1", "k2": "v2" })
        ```
        """
        if dimensions is None:
            # TODO add ability to define failure strategy
            return

        self.dimensions.append(dimensions)

    def set_dimensions(self, dimensionSets: List[Dict[str, str]]) -> None:
        """
        Overwrite all dimensions.
        ```
        context.set_dimensions([
            { "k1": "v1" },
            { "k1": "v1", "k2": "v2" }])
        ```
        """
        self.should_use_default_dimensions = False
        self.dimensions = dimensionSets

    def set_default_dimensions(self, default_dimensions: Dict) -> None:
        """
        Sets default dimensions for all other dimensions that get added
        to the context.
        If no custom dimensions are specified, the metrics will be emitted
        with the defaults.
        If custom dimensions are specified, they will be prepended with
        the default dimensions.
        """
        self.default_dimensions = default_dimensions

    def set_property(self, key: str, value: Any) -> None:
        self.properties[key] = value

    def get_dimensions(self) -> List[Dict]:
        """
        Returns the current dimensions on the context
        """
        # user has directly called set_dimensions
        if not self.should_use_default_dimensions:
            return self.dimensions

        if not self.__has_default_dimensions():
            return self.dimensions

        if len(self.dimensions) == 0:
            return [self.default_dimensions]

        # we have to merge dimensions on the read path
        # because defaults won't actually get set until the flush
        # method is called. This allows us to not block the user
        # code while we're detecting the environment
        return list(
            map(lambda custom: {**self.default_dimensions, **custom}, self.dimensions)
        )

    def __has_default_dimensions(self) -> bool:
        return self.default_dimensions is not None and len(self.default_dimensions) > 0

    def create_copy_with_context(self) -> "MetricsContext":
        """
        Creates a deep copy of the context excluding metrics.
        """
        new_properties: Dict = {}
        new_properties.update(self.properties)

        # dimensions added with put_dimension will not be copied.
        # the reason for this is so that you can flush the same scope multiple
        # times without stacking new dimensions. Example:
        #
        # @metric_scope
        # def my_func(metrics):
        #  metrics.put_dimensions(...)
        #
        # my_func()
        # my_func()
        new_dimensions: List[Dict] = []

        new_default_dimensions: Dict = {}
        new_default_dimensions.update(self.default_dimensions)

        return MetricsContext(
            self.namespace, new_properties, new_dimensions, new_default_dimensions
        )

    @staticmethod
    def empty() -> "MetricsContext":
        return MetricsContext()
