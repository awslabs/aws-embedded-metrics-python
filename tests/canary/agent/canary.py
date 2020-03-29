import asyncio
import aws_embedded_metrics
from aws_embedded_metrics import metric_scope
from aws_embedded_metrics.config import get_config
from getversion import get_module_version
import os
import psutil
import time
import logging


log = logging.getLogger(__name__)
version, _ = get_module_version(aws_embedded_metrics)
Config = get_config()
Config.log_group_name = '/Canary/Python/CloudWatchAgent/Metrics'
process = psutil.Process(os.getpid())


@metric_scope
async def app(init, last_run_duration, metrics):
    if init:
        metrics.put_metric('Init', 1, 'Count')

    init = False
    metrics.set_namespace('Canary')
    metrics.set_dimensions({"Runtime": 'Python', "Platform": 'ECS', "Agent": 'CloudWatchAgent', "Version": version})
    metrics.put_metric('Invoke', 1, "Count")
    metrics.put_metric('Duration', last_run_duration, 'Seconds')
    metrics.put_metric('Memory.RSS', process.memory_info().rss, 'Bytes')


async def main():
    init = True
    duration = None
    # wait for agent to start
    # TODO: this should not be needed if we're using a ring buffer to queue and re-try events
    await asyncio.sleep(10)
    while True:
        # capture the approximate run time of the method
        last_run_at = time.time_ns()
        await app(init, duration)
        duration = time.time_ns() - last_run_at
        await asyncio.sleep(0.2)
        init = False

asyncio.run(main())
