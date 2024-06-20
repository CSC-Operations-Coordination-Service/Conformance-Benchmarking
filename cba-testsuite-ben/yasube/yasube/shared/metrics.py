from enum import Enum
from typing import Any, Iterable

from yasube.utils.json import ExtendedJSONEncoder


class MetricName(Enum):
    ANALYSIS_TIME = "analysisTime"
    AVG_CONCURRENCY = "avgConcurrency"
    AVG_DATA_AVAILABILITY_LATENCY = "avgDataAvailabilityLatency"
    AVG_DATA_OPERATIONAL_LATENCY = "avgDataOperationalLatency"
    AVG_PRODUCT_RETENTION = "avgProductRetention"
    AVG_RESPONSE_TIME = "avgResponseTime"
    AVG_SIZE = "avgSize"
    BEGIN_GET_RESPONSE_TIME = "beginGetResponseTime"
    CATALOGUE_COVERAGE = "catalogueCoverage"
    DATA_COLLECTION_DIVISION = "dataCollectionDivision"
    DATA_COVERAGE = "dataCoverage"
    DATA_OFFER_CONSISTENCY = "dataOfferConsistency"
    DOWNLOAD_ELAPSED_TIME = "downloadElapsedTime"
    END_GET_RESPONSE_TIME = "endGetResponseTime"
    END_TIME = "endTime"
    ERROR_RATE = "errorRate"
    EXCEPTION = "exception"
    HTTP_STATUS_CODE = "httpStatusCode"
    MAX_DATA_AVAILABILITY_LATENCY = "maxDataAvailabilityLatency"
    MAX_DATA_OPERATIONAL_LATENCY = "maxDataOperationalLatency"
    MAX_RETRY_NUMBER = "maxRetryNumber"
    MAX_SIZE = "maxSize"
    MAX_TOTAL_RESULTS = "maxTotalResults"
    OFFLINE_DATA_AVAILABILITY_LATENCY = "offlineDataAvailabilityLatency"
    PEAK_CONCURRENCY = "peakConcurrency"
    PEAK_RESPONSE_TIME = "peakResponseTime"
    PRODUCT_RETENTION = "ProductRetention"
    QUERY_TIME = "queryTime"
    RESPONSE_RATE = "responseRate"
    RESPONSE_TIME = "responseTime"
    RESULTS_ERROR_RATE = "resultsErrorRate"
    RETRY_NUMBER = "retryNumber"
    SIZE = "size"
    START_TIME = "startTime"
    THROUGHPUT = "throughput"
    TOTAL_ONLINE_RESULTS = "totalOnlineResults"
    TOTAL_READ_RESULTS = "totalReadResults"
    TOTAL_REFERENCE_RESULTS = "totalReferenceResults"
    TOTAL_RESULTS = "totalResults"
    TOTAL_SIZE = "totalSize"
    TOTAL_VALIDATED_RESULTS = "totalValidatedResults"
    TOTAL_WRONG_RESULTS = "totalWrongResults"
    URL = "url"
    WRONG_RESULTS_COUNT = "wrongResultsCount"


class MetricUom(Enum):
    BOOLEAN = "bool"
    BYTES = "bytes"
    BYTES_SEC = "bytes/s"
    CODE = "code"
    COUNT = "#"
    DATETIME = "dateTime"
    DAYS = "days"
    MS = "ms"
    PERCENTAGE = "%"


class Metric(ExtendedJSONEncoder):
    def __init__(self, name: MetricName, uom: MetricUom, value: Any = None):
        self.name = name
        self.uom = uom
        self.value = value

    def __iter__(self):
        if isinstance(self.value, Iterable):
            return iter(self.value)
        else:
            raise TypeError("'Metric' object is not iterable")

    def __len__(self):
        if isinstance(self.value, Iterable):
            return len(self.value)
        else:
            raise TypeError("object of type 'Metric' has no len()")

    def set_value(self, value: Any) -> None:
        self.value = value

    def append(self, value) -> None:
        if isinstance(self.value, list):
            self.value.append(value)
        else:
            raise TypeError(f"{type(self.value)} does not have and 'append' method")

    def to_json(self) -> dict:
        return {
            "name": self.name.value,
            "uom": self.uom.value,
            "value": self.value,
        }
