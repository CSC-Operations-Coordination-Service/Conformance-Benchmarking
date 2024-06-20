from cba.cases.test_case_801 import TestCase801
from cba.cases.test_case_811 import TestCase811
from yasube.cases.base import BaseDetailTestCase, BaseListTestCase
from yasube.scenarios.base import BaseTestDetailScenario


class TestScenario10(BaseTestDetailScenario):

    list_test_case_class: BaseListTestCase = TestCase801
    detail_test_case_class: BaseDetailTestCase = TestCase811
