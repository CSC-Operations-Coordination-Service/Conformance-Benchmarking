import datetime
import time
from shutil import copyfileobj
from tempfile import NamedTemporaryFile
from typing import List, Tuple, Union

import prefect
import requests
from prefect.engine import signals

from yasube.shared.metrics import Metric, MetricName, MetricUom
from yasube.shared.test_case import MaxRetryExceeded, TestCase
from yasube.shared.url_helper import UrlHelper
from yasube.utils.urls import urlfilename


# ------------------------------------------------------------------
# Mixins
# ------------------------------------------------------------------
class GetMixin:
    def get(
        self, url: str, timeout: Union[float, None] = None, delay: Union[float, None] = None, stream: bool = False
    ) -> Tuple[List[Metric], requests.Response]:
        response = None
        metrics: List[Metric] = []
        try:
            self.logger.info(f"Requesting url {url} with a timeout of {timeout} seconds")
            metrics.append(Metric(MetricName.START_TIME, MetricUom.DATETIME, datetime.datetime.utcnow()))
            response: requests.Response = self.platform.session.get(
                url=url, timeout=timeout, stream=stream, verify=self.platform.verify_ssl
            )
            metrics.append(Metric(MetricName.HTTP_STATUS_CODE, MetricUom.CODE, response.status_code))
            response.raise_for_status()
            if stream:
                filename = urlfilename(response)
                self.logger.info(f"Start downloading {filename}")
        except requests.exceptions.RequestException as exc:
            try:
                self.logger.error(f"Request failed, retrying: {exc}")
                self.reraise_until_exhausted(exc)
            except MaxRetryExceeded as exc:
                # TODO We should add a metric with a shortened description of the occured error
                # or find a way to let the error bubble up so that we can write it down into
                # the results file.
                self.logger.error(f"Request failed: {exc.original}")
                metrics.append(Metric(MetricName.RESPONSE_TIME, MetricUom.MS, -1))
                metrics.append(Metric(MetricName.SIZE, MetricUom.BYTES, -1))
                metrics.append(Metric(MetricName.EXCEPTION, MetricUom.BOOLEAN, True))
        else:
            response_time = response.elapsed.total_seconds() * 1000
            self.logger.debug(f"Response time: {response_time} ms")
            metrics.append(Metric(MetricName.RESPONSE_TIME, MetricUom.MS, response_time))
            metrics.append(Metric(MetricName.EXCEPTION, MetricUom.BOOLEAN, False))
            if stream:
                with NamedTemporaryFile() as fp:
                    copyfileobj(response.raw, fp, length=1000)
                    metrics.append(Metric(MetricName.END_TIME, MetricUom.DATETIME, datetime.datetime.utcnow()))
                    filename = urlfilename(response)
                    size = fp.tell()
                    self.logger.info(f"Finished downloading {filename} of {size} bytes")
                    metrics.append(Metric(MetricName.SIZE, MetricUom.BYTES, size))
            else:
                metrics.append(Metric(MetricName.END_TIME, MetricUom.DATETIME, datetime.datetime.utcnow()))
                metrics.append(Metric(MetricName.SIZE, MetricUom.BYTES, len(response.content)))

        finally:
            if delay is not None:
                time.sleep(delay)

        return metrics, response


# ------------------------------------------------------------------
# Base classes
# ------------------------------------------------------------------


class BaseListTestCase(TestCase, GetMixin):
    """
    Base class for list test case.
    It submits predefined requests to a list-like endpoint, gathering Metrics along the way.

    Subclasses are only expected to specify the resource path, which will be appended to the
    platform root uri.

    The query (if any) is specified in the configuration file and can use a number of
    templates that will be replaced at runtime to allow for custom date range, random
    product types or geographic information.
    """

    class Meta:
        key = "Base List Test Case"
        name = "Base test case for a list GET request"
        resource_path = None

    def build_url(self) -> str:
        return UrlHelper.build(self.platform.root_uri, self._meta.resource_path, self.config.get("query"))

    def run(self, index: int = 1, total: int = 1) -> Tuple[List[Metric], requests.Response]:
        self.logger.info(f"Request {index} out of {total}")
        metrics, response = self.get(
            self.build_url(),
            self.config.get("requests_timeout"),
            self.config.get("requests_delay"),
        )
        self._append_response_metrics(response, metrics)

        return metrics, response

    def append_extra_response_metrics(self, response: requests.Response, metrics: List[Metric]):
        """Hook method to be overriden by subclasses in case of specific metrics."""
        pass

    def _append_response_metrics(self, response: requests.Response, metrics: List[Metric]):
        self._append_total_read_results(response, metrics)
        self.append_extra_response_metrics(response, metrics)

    def _append_total_read_results(self, response: requests.Response, metrics: List[Metric]):
        total_results = 0
        if response is not None and response.status_code == 200:
            total_results = len(response.json()["value"])

            if self.config.get("ensure_results"):
                task_run_count = prefect.context.get("task_run_count")
                if total_results == 0 and task_run_count <= self.max_retries:
                    self.logger.info(f"Found {total_results} items, retrying ({task_run_count}/{self.max_retries})...")
                    raise signals.RETRY

            self.logger.info(f"Found {total_results} items")

        metrics.append(Metric(MetricName.TOTAL_READ_RESULTS, MetricUom.COUNT, total_results))


class BaseDetailTestCase(TestCase, GetMixin):
    """
    Base class for detail test case.
    It submits predefined requests to a detail-like endpoint, gathering Metrics along the way.

    Subclasses are only expected to specify the resource path, which will be appended to the
    platform root uri, followed by the primary key.
    """

    class Meta:
        key = "Base Detail Test Case"
        name = "Base test case for a detail GET request"
        resource_path = None

    def build_url(self, pk: str) -> str:
        return UrlHelper.build(self.platform.root_uri, f"{self._meta.resource_path}({pk})")

    def run(self, pk: Union[str, int]) -> Tuple[List[Metric], requests.Response]:
        return self.get(self.build_url(pk))


class BaseDownloadTestCase(BaseDetailTestCase):
    """
    Base class for a download test case.
    It is similar to the parent class, but the response is streamed
    to a temporary file and not read in memory.
    """

    def run(self, pk: Union[str, int]) -> Tuple[List[Metric], requests.Response]:
        return self.get(self.build_url(pk), stream=True)
