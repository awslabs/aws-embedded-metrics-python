from aws_embedded_metrics.metric_scope import metric_scope


@metric_scope
def my_handler(event, context, metrics):
    metrics.put_dimensions({"Foo": "Bar"})
    metrics.put_metric("ProcessingLatency", 100, "Milliseconds")
    metrics.set_property("AccountId", "123456789012")
    metrics.set_property("RequestId", "422b1569-16f6-4a03-b8f0-fe3fd9b100f8")
    metrics.set_property("DeviceId", "61270781-c6ac-46f1-baf7-22c808af8162")
    metrics.set_property(
        "Payload", {"sampleTime": 123456789, "temperature": 273.0, "pressure": 101.3}
    )

    return {"message": "Hello!"}
