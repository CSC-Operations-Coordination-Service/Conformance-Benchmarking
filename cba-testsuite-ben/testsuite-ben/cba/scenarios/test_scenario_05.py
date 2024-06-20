from typing import List

from yasube.scenarios.base import BaseTestListScenario
from yasube.shared.metrics import MetricName

from cba.cases.test_case_001 import TestCase001
from cba.cases.test_case_701 import TestCase701


class TestScenario05(BaseTestListScenario):

    def get_list_test_case_class(self):
        if "CADIP" in self.platform.key:
            return TestCase701
        else:
            return TestCase001

    @property
    def expected_metrics(self) -> List[MetricName]:
        return [
            MetricName.AVG_RESPONSE_TIME,
            MetricName.PEAK_RESPONSE_TIME,
            MetricName.ERROR_RATE,
        ]
