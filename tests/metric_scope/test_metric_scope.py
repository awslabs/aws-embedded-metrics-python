from aws_embedded_metrics.metric_scope import metric_scope
from aws_embedded_metrics.logger.metrics_logger import MetricsLogger
from aws_embedded_metrics.config import get_config
import asyncio
import time
import pytest

flush_invocations = []


@pytest.fixture
def mock_logger(mocker):
    InvocationTracker.reset()

    async def flush(self):
        print("flush called")
        InvocationTracker.record()

    MetricsLogger.flush = flush


@pytest.mark.asyncio
async def test_async_scope_executes_handler_function(mock_logger):
    # arrange
    test_input = {}

    @metric_scope
    async def my_handler(test_input):
        await asyncio.sleep(1)
        test_input["wasExecuted"] = True

    # act
    await my_handler(test_input)

    # assert
    assert test_input["wasExecuted"] is True


def test_sync_scope_executes_handler_function(mock_logger):
    # arrange
    test_input = {}

    @metric_scope
    def my_handler(test_input):
        test_input["wasExecuted"] = True

    # act
    my_handler(test_input)

    # assert
    assert test_input["wasExecuted"] is True


@pytest.mark.asyncio
async def test_async_scope_forwards_handler_return_value(mock_logger):
    # arrange
    expected_result = True

    @metric_scope
    async def my_handler():
        await asyncio.sleep(1)
        return expected_result

    # act
    actual_result = await my_handler()

    # assert
    assert expected_result == actual_result


def test_sync_scope_forwards_handler_return_value(mock_logger):
    # arrange
    expected_result = True

    @metric_scope
    def my_handler():
        return expected_result

    # act
    actual_result = my_handler()

    # assert
    assert expected_result == actual_result


@pytest.mark.asyncio
async def test_async_scope_passes_configured_metrics_logger(mock_logger):
    # arrange
    @metric_scope
    async def my_handler(metrics):
        await asyncio.sleep(1)
        return metrics

    # act
    actual_result = await my_handler()

    # assert
    assert isinstance(actual_result, MetricsLogger)


def test_sync_scope_passes_configured_metrics_logger(mock_logger):
    # arrange
    @metric_scope
    def my_handler(metrics):
        return metrics

    # act
    actual_result = my_handler()

    # assert
    assert isinstance(actual_result, MetricsLogger)


@pytest.mark.asyncio
async def test_async_scope_handles_exceptions(mock_logger):
    exceptions_thrown = 0

    # arrange
    @metric_scope
    async def my_handler(metrics):
        await asyncio.sleep(1)
        raise Exception("Something bad happened")

    # act
    try:
        await my_handler()
    except Exception:
        exceptions_thrown = 1

    # assert
    assert exceptions_thrown == 1
    assert InvocationTracker.invocations == 1


def test_sync_scope_handles_exceptions(mock_logger):
    exceptions_thrown = 0

    # arrange
    @metric_scope
    def my_handler(metrics):
        raise Exception("Something bad happened")

    # act
    try:
        my_handler()
    except Exception:
        exceptions_thrown = 1

    # assert
    assert exceptions_thrown == 1
    assert InvocationTracker.invocations == 1


def test_sync_scope_sets_time_based_on_when_wrapped_fcn_is_called(mock_logger):
    # arrange
    sleep_duration_sec = 3

    @metric_scope
    def my_handler(metrics):
        return metrics

    time.sleep(sleep_duration_sec)

    # act
    expected_timestamp_second = int(round(time.time()))
    logger = my_handler()

    # assert
    actual_timestamp_second = int(round(logger.context.meta["Timestamp"] / 1000))
    assert expected_timestamp_second == actual_timestamp_second


@pytest.mark.asyncio
async def test_async_generator_completes_successfully(mock_logger):
    expected_results = [1, 2, 3]

    @metric_scope
    async def my_handler():
        for item in expected_results:
            yield item

    actual_results = []
    async for result in my_handler():
        actual_results.append(result)

    assert actual_results == expected_results
    # TODO in v4: change to 1 — default_flush_on_yield becomes False, flushing only once at completion
    assert InvocationTracker.invocations == 4  # 3 yields + 1 final flush


def test_sync_generator_completes_successfully(mock_logger):
    expected_results = [1, 2, 3]

    @metric_scope
    def my_handler():
        yield from expected_results

    actual_results = []
    for result in my_handler():
        actual_results.append(result)

    assert actual_results == expected_results
    # TODO in v4: change to 1 — default_flush_on_yield becomes False, flushing only once at completion
    assert InvocationTracker.invocations == 4  # 3 yields + 1 final flush

def test_sync_generator_handles_exception(mock_logger):
    expected_results = [1, 2]

    @metric_scope
    def my_handler():
        yield from expected_results
        raise Exception("test exception")

    actual_results = []
    with pytest.raises(Exception, match="test exception"):
        for result in my_handler():
            actual_results.append(result)

    assert actual_results == expected_results
    # TODO in v4: change to 1 — default_flush_on_yield becomes False, flushing only once at completion
    assert InvocationTracker.invocations == 3


@pytest.mark.asyncio
async def test_async_generator_handles_exception(mock_logger):
    expected_results = [1, 2]

    @metric_scope
    async def my_handler():
        for item in expected_results:
            yield item
            await asyncio.sleep(1)
        raise Exception("test exception")

    actual_results = []
    with pytest.raises(Exception, match="test exception"):
        async for result in my_handler():
            actual_results.append(result)

    assert actual_results == expected_results
    # TODO in v4: change to 1 — default_flush_on_yield becomes False, flushing only once at completion
    assert InvocationTracker.invocations == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("flush_on_yield, expected_num_of_flushes", [(True, 4), (False, 1)])
async def test_async_generator_flush_on_yield_set_via_decorator(mock_logger, flush_on_yield, expected_num_of_flushes):
    expected_results = [1, 2, 3]

    @metric_scope(flush_on_yield=flush_on_yield)
    async def my_handler():
        for item in expected_results:
            yield item

    actual_results = []
    async for result in my_handler():
        actual_results.append(result)

    assert actual_results == expected_results
    assert InvocationTracker.invocations == expected_num_of_flushes


@pytest.mark.parametrize("flush_on_yield, expected_num_of_flushes", [(True, 4), (False, 1)])
def test_sync_generator_flush_on_yield_set_via_decorator(mock_logger, flush_on_yield, expected_num_of_flushes):
    expected_results = [1, 2, 3]

    @metric_scope(flush_on_yield=flush_on_yield)
    def my_handler():
        yield from expected_results

    actual_results = []
    for result in my_handler():
        actual_results.append(result)

    assert actual_results == expected_results
    assert InvocationTracker.invocations == expected_num_of_flushes


@pytest.mark.asyncio
@pytest.mark.parametrize("flush_on_yield, expected_num_of_flushes", [(True, 4), (False, 1)])
async def test_async_generator_respects_default_config_flush_on_yield(mock_logger, flush_on_yield, expected_num_of_flushes):
    original_flush_on_yield = get_config().default_flush_on_yield
    get_config().default_flush_on_yield = flush_on_yield
    try:
        expected_results = [1, 2, 3]

        @metric_scope
        async def my_handler():
            for item in expected_results:
                yield item

        actual_results = []
        async for result in my_handler():
            actual_results.append(result)

        assert actual_results == expected_results
        assert InvocationTracker.invocations == expected_num_of_flushes
    finally:
        get_config().default_flush_on_yield = original_flush_on_yield


@pytest.mark.parametrize("flush_on_yield, expected_num_of_flushes", [(True, 4), (False, 1)])
def test_sync_generator_respects_default_config_flush_on_yield(mock_logger, flush_on_yield, expected_num_of_flushes):
    original_flush_on_yield = get_config().default_flush_on_yield
    get_config().default_flush_on_yield = flush_on_yield
    try:
        expected_results = [1, 2, 3]

        @metric_scope
        def my_handler():
            yield from expected_results

        actual_results = []
        for result in my_handler():
            actual_results.append(result)

        assert actual_results == expected_results
        assert InvocationTracker.invocations == expected_num_of_flushes
    finally:
        get_config().default_flush_on_yield = original_flush_on_yield


# Test helpers


class InvocationTracker(object):
    invocations = 0

    @staticmethod
    def record():
        InvocationTracker.invocations += 1

    @staticmethod
    def reset():
        InvocationTracker.invocations = 0
