from cba.cases.test_case_701 import TestCase701
from cba.cases.test_case_711 import TestCase711
from yasube.cases.base import BaseDetailTestCase, BaseListTestCase
from yasube.scenarios.base import BaseTestDetailScenario


class TestScenario07(BaseTestDetailScenario):

    list_test_case_class: BaseListTestCase = TestCase701
    detail_test_case_class: BaseDetailTestCase = TestCase711
