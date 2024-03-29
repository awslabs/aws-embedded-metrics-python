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
from aws_embedded_metrics.storage_resolution import StorageResolution


class Metric(object):
    def __init__(self, value: float, unit: str = None, storage_resolution: StorageResolution = StorageResolution.STANDARD):
        self.values = [value]
        self.unit = unit or "None"
        self.storage_resolution = storage_resolution or StorageResolution.STANDARD

    def add_value(self, value: float) -> None:
        self.values.append(value)
