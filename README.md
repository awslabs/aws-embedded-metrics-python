# aws-embedded-metrics

![](https://codebuild.us-west-2.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoidjNkYXpXTzMxdUY2dEdab2RaZTgvTXhUSGh2bjNmUlhmUEorejM0UytyOWNqeFptcUpBT2wzNkJ1MkExQXI3UFdNaGQzNlVmSzBPWkRhdmhkb2lqL05NPSIsIml2UGFyYW1ldGVyU3BlYyI6IkhKZS9rd2UwYzVud1VucVgiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=master)
[![](https://img.shields.io/pypi/v/aws-embedded-metrics)](https://pypi.org/project/aws-embedded-metrics/)

Generate CloudWatch Metrics embedded within structured log events. The embedded metrics will be extracted so you can visualize and alarm on them for real-time incident detection. This allows you to monitor aggregated values while preserving the detailed event context that generated them.

- [Use Cases](#use-cases)
- [Installation](#installation)
- [Usage](#usage)
- [API](#api)
- [Examples](#examples)
- [Development](#development)

## Use Cases

- **Generate custom metrics across compute environments**

  - Easily generate custom metrics from Lambda functions without requiring custom batching code, making blocking network requests or relying on 3rd party software.
  - Other compute environments (EC2, On-prem, ECS, EKS, and other container environments) are supported by installing the [CloudWatch Agent](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Generation_CloudWatch_Agent.html).

- **Linking metrics to high cardinality context**

  Using the Embedded Metric Format, you will be able to visualize and alarm on custom metrics, but also retain the original, detailed and high-cardinality context which is queryable using [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html). For example, the library automatically injects environment metadata such as Lambda Function version, EC2 instance and image ids into the structured log event data.

## Installation

```
pip3 install aws-embedded-metrics
```

## Usage

To get a metric logger, you can decorate your function with a `metric_scope`:

```py
from aws_embedded_metrics import metric_scope

@metric_scope
def my_handler(metrics):
    metrics.put_dimensions({"Foo": "Bar"})
    metrics.put_metric("ProcessingLatency", 100, "Milliseconds")
    metrics.set_property("AccountId", "123456789012")
    metrics.set_property("RequestId", "422b1569-16f6-4a03")
    metrics.set_property("DeviceId", "61270781-c6ac-46f1")

    return {"message": "Hello!"}
```

## API

### MetricsLogger

The `MetricsLogger` is the interface you will use to publish embedded metrics.

- **put_metric**(key: str, value: float, unit: str = "None") -> MetricsLogger

Adds a new metric to the current logger context. Multiple metrics using the same key will be appended to an array of values. The Embedded Metric Format supports a maximum of 100 values per key. If more metric values are added than are supported by the format, the logger will be flushed to allow for new metric values to be captured.

Requirements:

- Name Length 1-255 characters
- Name must be ASCII characters only
- Values must be in the range of 8.515920e-109 to 1.174271e+108. In addition, special values (for example, NaN, +Infinity, -Infinity) are not supported.
- Units must meet CW Metrics unit requirements, if not it will default to None. See [MetricDatum](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/API_MetricDatum.html) for valid values.

Examples:

```py
put_metric("Latency", 200, "Milliseconds")
```

- **set_property**(key: str, value: Any) -> MetricsLogger

Adds or updates the value for a given property on this context. This value is not submitted to CloudWatch Metrics but is searchable by CloudWatch Logs Insights. This is useful for contextual and potentially high-cardinality data that is not appropriate for CloudWatch Metrics dimensions.

Requirements:

- Length 1-255 characters

Examples:

```py
set_property("RequestId", "422b1569-16f6-4a03-b8f0-fe3fd9b100f8")
set_property("InstanceId", "i-1234567890")
set_property("Device", {
  "Id": "61270781-c6ac-46f1-baf7-22c808af8162",
  "Name": "Transducer",
  "Model": "PT-1234"
})
```

- **put_dimensions**(dimensions: Dict[str, str]) -> MetricsLogger

Adds a new set of dimensions that will be associated to all metric values.

**WARNING**: Every distinct value will result in a new CloudWatch Metric.
If the cardinality of a particular value is expected to be high, you should consider
using `setProperty` instead.

Requirements:

- Length 1-255 characters
- ASCII characters only

Examples:

```py
put_dimensions({ "Operation": "Aggregator" })
put_dimensions({ "Operation": "Aggregator", "DeviceType": "Actuator" })
```

- **set_dimensions**(\*dimensions: Dict[str, str]) -> MetricsLogger

Explicitly override all dimensions. This will remove the default dimensions.

**WARNING**: Every distinct value will result in a new CloudWatch Metric.
If the cardinality of a particular value is expected to be high, you should consider
using `setProperty` instead.

Requirements:

- Length 1-255 characters
- ASCII characters only

Examples:

```py
set_dimensions(
  { "Operation": "Aggregator" },
  { "Operation": "Aggregator", "DeviceType": "Actuator" }
)
```

- **set_namespace**(value: str) -> MetricsLogger

Sets the CloudWatch [namespace](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html#Namespace) that extracted metrics should be published to. If not set, a default value of aws-embedded-metrics will be used.

Requirements:

- Name Length 1-255 characters
- Name must be ASCII characters only

Examples:

```py
set_namespace("MyApplication")
```

- **flush**()

Flushes the current MetricsContext to the configured sink and resets all properties, dimensions and metric values. The namespace and default dimensions will be preserved across flushes.

### Configuration

All configuration values can be set using environment variables with the prefix (`AWS_EMF_`). Configuration should be performed as close to application start up as possible.

**ServiceName**: Overrides the name of the service. For services where the name cannot be inferred (e.g. Java process running on EC2), a default value of Unknown will be used if not explicitly set.

Requirements:

- Name Length 1-255 characters
- Name must be ASCII characters only

Example:

```py
# in process
from aws_embedded_metrics.config import get_config
Config = get_config()
Config.service_name = "MyApp"

# environment
AWS_EMF_SERVICE_NAME = MyApp
```

**ServiceType**: Overrides the type of the service. For services where the type cannot be inferred (e.g. Java process running on EC2), a default value of Unknown will be used if not explicitly set.

Requirements:

- Name Length 1-255 characters
- Name must be ASCII characters only

Example:

```py
# in process
from aws_embedded_metrics.config import get_config
Config = get_config()
Config.service_type = "NodeJSWebApp"

# environment
AWS_EMF_SERVICE_TYPE = NodeJSWebApp
```

**LogGroupName**: For agent-based platforms, you may optionally configure the destination log group that metrics should be delivered to. This value will be passed from the library to the agent in the Embedded Metric payload. If a LogGroup is not provided, the default value will be derived from the service name: <service-name>-metrics

Requirements:

- Name Length 1-512 characters
- Log group names consist of the following characters: a-z, A-Z, 0-9, '\_' (underscore), '-' (hyphen), '/' (forward slash), and '.' (period). Pattern: [\.\-_/#A-Za-z0-9]+

Example:

```py
# in process
from aws_embedded_metrics.config import get_config
Config = get_config()
Config.log_group_name = "LogGroupName"

# environment
AWS_EMF_LOG_GROUP_NAME = LogGroupName
```

**LogStreamName**: For agent-based platforms, you may optionally configure the destination log stream that metrics should be delivered to. This value will be passed from the library to the agent in the Embedded Metric payload. If a LogGroup is not provided, the default value will be derived by the agent (this will likely be the hostname).

Requirements:

- Name Length 1-512 characters
- The ':' (colon) and '\*' (asterisk) characters are not allowed. Pattern: [^:]\*

Example:

```py
# in process
from aws_embedded_metrics.config import get_config
Config = get_config()
Config.log_stream_name = "LogStreamName"

# environment
AWS_EMF_LOG_STREAM_NAME = LogStreamName
```

**NameSpace**: Overrides the CloudWatch [namespace](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch_concepts.html#Namespace). If not set, a default value of aws-embedded-metrics will be used.

Requirements:

- Name Length 1-512 characters
- Name must be ASCII characters only

Example:

```py
# in process
from aws_embedded_metrics.config import get_config
Config = get_config()
Config.namespace = "MyApplication"

# environment
AWS_EMF_NAMESPACE = MyApplication
```

## Examples

Check out the [examples](https://github.com/awslabs/aws-embedded-metrics-python/tree/master/examples) directory to get started.

## Development

1. Install Test Dependencies

```
pip install tox
```

2. Run tests

```
tox
```

3. Integration tests. These tests require Docker to run the CloudWatch Agent and valid AWS credentials. Tests can be run by:

```sh
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export AWS_REGION=us-west-2
./bin/run-integ-tests.sh
```

## License

This project is licensed under the Apache-2.0 License.
