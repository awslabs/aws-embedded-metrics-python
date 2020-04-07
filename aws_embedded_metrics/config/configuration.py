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


class Configuration:
    def __init__(
        self,
        debug_logging_enabled: bool,
        service_name: str,
        service_type: str,
        log_group_name: str,
        log_stream_name: str,
        agent_endpoint: str,
        ec2_metadata_endpoint: str = None,
        namespace: str = None,
    ):
        self.debug_logging_enabled = debug_logging_enabled
        self.service_name = service_name
        self.service_type = service_type
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.agent_endpoint = agent_endpoint
        self.ec2_metadata_endpoint = ec2_metadata_endpoint
        self.namespace = namespace
