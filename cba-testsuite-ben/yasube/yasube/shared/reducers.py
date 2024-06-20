import datetime
from typing import Any, List, Union

import prefect

from yasube.shared.metrics import Metric, MetricName, MetricUom


def rate(results: List[Union[int, float]], value=-1):
    estimated = len([r for r in results if r == value])
    actual = len(results) or 1
    return 100 - abs(estimated - actual) / actual * 100


def average(results: List[Union[int, float]], default: int = -1) -> int:
    if all([r < 0 for r in results]):
        # Special case: all results are negative. We return the default in this case.
        return default
    else:
        # Otherwise we filter out possible errors
        results = [r for r in results if r > 0]
        return round(sum(results) / (len(results) or 1))


class MetricReducer:
    @staticmethod
    def reduce_avg_response_time(results: List[Metric]) -> Metric:
        response_times = [
            r.value for r in results if r.name == MetricName.RESPONSE_TIME
        ]
        avg_response_time = average(response_times)
        return Metric(MetricName.AVG_RESPONSE_TIME, MetricUom.MS, avg_response_time)

    @staticmethod
    def reduce_avg_product_retention(results: List[Metric]) -> Metric:
        product_retentions = [
            r.value for r in results if r.name == MetricName.PRODUCT_RETENTION
        ]
        avg_product_retention = average(product_retentions)
        return Metric(
            MetricName.AVG_PRODUCT_RETENTION, MetricUom.DAYS, avg_product_retention
        )

    @staticmethod
    def reduce_peak_response_time(results: List[Metric]) -> Metric:
        response_times = [
            r.value for r in results if r.name == MetricName.RESPONSE_TIME
        ]
        try:
            peak = round(max(response_times))
        except ValueError:
            peak = 0

        return Metric(MetricName.PEAK_RESPONSE_TIME, MetricUom.MS, peak)

    @staticmethod
    def reduce_error_rate(results: List[Metric]) -> Metric:
        exceptions = [r.value for r in results if r.name == MetricName.EXCEPTION]
        return Metric(
            MetricName.ERROR_RATE, MetricUom.PERCENTAGE, rate(exceptions, True)
        )

    @staticmethod
    def reduce_avg_size(results: List[Metric]) -> Metric:
        sizes = [r.value for r in results if r.name == MetricName.SIZE]
        avg_size = average(sizes)
        return Metric(MetricName.AVG_SIZE, MetricUom.BYTES, avg_size)

    @staticmethod
    def reduce_max_size(results: List[Metric]) -> Metric:
        sizes = [r.value for r in results if r.name == MetricName.SIZE]
        try:
            max_size = round(max(sizes))
        except ValueError:
            max_size = 0

        return Metric(MetricName.MAX_SIZE, MetricUom.BYTES, max_size)

    @staticmethod
    def reduce_throughput(results: List[Metric]) -> Metric:
        logger = prefect.context.get("logger")
        start_times = []
        end_times = []
        response_times = []
        sizes = []

        for metric in results:
            if metric.name == MetricName.START_TIME:
                start_times.append(metric.value)
            elif metric.name == MetricName.END_TIME:
                end_times.append(metric.value)
            elif metric.name == MetricName.RESPONSE_TIME:
                response_times.append(metric.value)
            elif metric.name == MetricName.SIZE:
                sizes.append(metric.value)

        adjusted_start_times = []
        for i, start_time in enumerate(start_times):
            adjusted_start_times.append(
                start_time + datetime.timedelta(milliseconds=response_times[i])
            )

        throughput = -1
        if adjusted_start_times:
            start = min(adjusted_start_times)
            end = max(end_times)
            size = sum(sizes)
            elapsed_time = ((end - start).total_seconds()) or 1
            throughput = round(size / elapsed_time, 2)
            logger.info(
                f"Size: {size} Elapsed: {elapsed_time} Throughput: {throughput}"
            )

        return Metric(MetricName.THROUGHPUT, MetricUom.BYTES_SEC, f"{throughput}")

    @staticmethod
    def reduce_total_read_results(results: List[Metric]) -> Metric:
        return Metric(
            MetricName.TOTAL_READ_RESULTS,
            MetricUom.COUNT,
            sum([r.value for r in results if r.name == MetricName.TOTAL_READ_RESULTS]),
        )
