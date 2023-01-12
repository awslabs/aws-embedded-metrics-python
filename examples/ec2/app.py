from aws_embedded_metrics import metric_scope
from aws_embedded_metrics.storageResolution import StorageResolution

import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@metric_scope
def my_handler(metrics):
    metrics.put_dimensions({"Foo": "Bar"})
    metrics.put_metric("ProcessingLatency", 100, "Milliseconds")
    metrics.put_metric("CPU Utilization", 87, "Percent", StorageResolution.HIGH)
    metrics.set_property("AccountId", "123456789012")
    metrics.set_property("RequestId", "422b1569-16f6-4a03-b8f0-fe3fd9b100f8")
    metrics.set_property("DeviceId", "61270781-c6ac-46f1-baf7-22c808af8162")
    metrics.set_property(
        "Payload", {"sampleTime": 123456789, "temperature": 273.0, "pressure": 101.3}
    )

    return {"message": "Hello!"}


my_handler()

log.info("Example completed.")
