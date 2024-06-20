import datetime
from typing import List

import requests
from yasube.cases.base import BaseListTestCase
from yasube.shared.metrics import Metric, MetricName, MetricUom

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class TestCase001(BaseListTestCase):
    class Meta:
        key = "TestCase001"
        name = "GET Products List"
        resource_path = "Products"

    def append_extra_response_metrics(self, response: requests.Response, metrics: List[Metric]):
        if response is not None and response.status_code == 200:
            products = response.json()["value"]
            for product in products:
                try:
                    eviction_date = datetime.datetime.strptime(product['EvictionDate'], DATETIME_FORMAT)
                    publication_date = datetime.datetime.strptime(product['PublicationDate'], DATETIME_FORMAT)
                    retention = (eviction_date - publication_date).days
                    metrics.append(Metric(MetricName.PRODUCT_RETENTION, MetricUom.DAYS, retention))
                except (KeyError, TypeError, ValueError):
                    metrics.append(Metric(MetricName.PRODUCT_RETENTION, MetricUom.DAYS, -1))