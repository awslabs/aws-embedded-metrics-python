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
    ):
        self.debug_logging_enabled = debug_logging_enabled
        self.service_name = service_name
        self.service_type = service_type
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.agent_endpoint = agent_endpoint
        self.ec2_metadata_endpoint = ec2_metadata_endpoint
