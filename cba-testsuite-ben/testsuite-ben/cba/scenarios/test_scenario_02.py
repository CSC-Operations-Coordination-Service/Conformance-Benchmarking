from yasube.cases.base import BaseDetailTestCase, BaseListTestCase
from yasube.scenarios.base import BaseTestDetailScenario

from cba.cases.test_case_001 import TestCase001
from cba.cases.test_case_011 import TestCase011


class TestScenario02(BaseTestDetailScenario):

    list_test_case_class: BaseListTestCase = TestCase001
    detail_test_case_class: BaseDetailTestCase = TestCase011
