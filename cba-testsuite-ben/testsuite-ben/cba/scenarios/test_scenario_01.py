from typing import List
from yasube.scenarios.base import BaseTestListScenario
from yasube.shared.metrics import MetricName

from cba.cases.test_case_001 import TestCase001


class TestScenario01(BaseTestListScenario):

    list_test_case_class = TestCase001

    @property
    def expected_metrics(self) -> List[MetricName]:
        values = super().expected_metrics
        values.append(MetricName.AVG_PRODUCT_RETENTION)
        return values
