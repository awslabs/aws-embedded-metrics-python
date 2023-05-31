# Examples

## Docker

With Docker images, using the `awslogs` log driver will send your container logs to CloudWatch Logs. All you have to do is write to STDOUT and your EMF logs will be processed.

[Official Docker documentation for `awslogs` driver](https://docs.docker.com/config/containers/logging/awslogs/)

## ECS and Fargate

With ECS and Fargate, you can use the `awslogs` log driver to have your logs sent to CloudWatch Logs on your behalf. After configuring your task to use the `awslogs` log driver, you may write your EMF logs to STDOUT and they will be processed.

[ECS documentation on `awslogs` log driver](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/using_awslogs.html)

## Fluent Bit and Fluentd

Fluent Bit can be used to collect logs and push them to CloudWatch Logs. After configuring the Amazon CloudWatch Logs output plugin, you may write your EMF logs to STDOUT and they will be processed.

[Getting Started with Fluent Bit](https://docs.fluentbit.io/manual/installation/getting-started-with-fluent-bit)

[Amazon CloudWatch output plugin for Fluent Bit](https://docs.fluentbit.io/manual/pipeline/outputs/cloudwatch)

### Example Metrics

```json
{
  "_aws": {
    "Timestamp": 1583902595342,
    "CloudWatchMetrics": [
      {
        "Dimensions": [[ "ServiceName", "ServiceType" ]],
        "Metrics": [{ "Name": "ProcessingTime", "Unit": "Milliseconds" }],
        "Namespace": "aws-embedded-metrics"
      }
    ]
  },
  "ServiceName": "example",
  "ServiceType": "AWS::ECS::Container",
  "Method": "GET",
  "Url": "/test",
  "containerId": "702e4bcf1345",
  "createdAt": "2020-03-11T04:54:24.981207801Z",
  "startedAt": "2020-03-11T04:54:25.594413051Z",
  "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/emf-examples:latest",
  "cluster": "emf-example",
  "taskArn": "arn:aws:ecs:<region>:<account-id>:task/2fe946f6-8a2e-41a4-8fec-c4983bad8f74",
  "ProcessingTime": 5
}
```
