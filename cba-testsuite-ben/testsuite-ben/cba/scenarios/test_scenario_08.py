from typing import Callable, Dict, List

from cba.cases.test_case_801 import TestCase801
from cba.cases.test_case_821 import TestCase821
from yasube.cases.base import BaseDetailTestCase, BaseListTestCase
from yasube.scenarios.base import BaseTestDetailScenario
from yasube.shared.metrics import MetricName


class TestScenario08(BaseTestDetailScenario):

    list_test_case_class: BaseListTestCase = TestCase801
    detail_test_case_class: BaseDetailTestCase = TestCase821

    def get_picking_filter(self, config: Dict) -> Callable[[Dict], bool]:
        max_download_size = config.get("max_download_size")
        def func(item: Dict) -> bool:
            if max_download_size is not None:
                return item.get("ContentLength", 0) < max_download_size
            return True

        return func

    @property
    def expected_metrics(self) -> List[MetricName]:
        return [
            MetricName.AVG_RESPONSE_TIME,
            MetricName.PEAK_RESPONSE_TIME,
            MetricName.AVG_SIZE,
            MetricName.MAX_SIZE,
            MetricName.THROUGHPUT,
            MetricName.ERROR_RATE,
        ]

