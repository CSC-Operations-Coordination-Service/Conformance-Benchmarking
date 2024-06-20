from typing import Callable, Dict, List

from prefect import Flow, case, flatten, unmapped

from yasube.cases.base import BaseDetailTestCase, BaseListTestCase
from yasube.cases.common import (check_empty_response, check_length,
                                 check_response_status, pick_random_pks,
                                 reduce_metrics, split_test_results,
                                 write_metrics)
from yasube.shared.metrics import MetricName
from yasube.shared.test_scenario import TestScenario


class BaseTestListScenario(TestScenario):
    list_test_case_class: BaseListTestCase

    @property
    def expected_metrics(self) -> List[MetricName]:
        return [
            MetricName.AVG_RESPONSE_TIME,
            MetricName.PEAK_RESPONSE_TIME,
            MetricName.ERROR_RATE,
            MetricName.TOTAL_READ_RESULTS,
        ]

    def get_list_test_case(self) -> BaseListTestCase:
        """
        Return the list test case instance, the primary task of the flow.
        The configuration is expected to have a key with the same name
        of the class, that will be passed to initialize the instance.
        """
        list_test_case_class = self.get_list_test_case_class()
        config = self.cases.get(list_test_case_class.__name__, {})
        return list_test_case_class(config, self.platform)

    def get_list_test_case_class(self) -> BaseListTestCase:
        """
        Return the class to use for the list test case.
        Defaults to using `self.list_test_case_class`.
        You may want to override this if you need to provide different
        test case class depending on other conditions.
        """
        assert self.list_test_case_class is not None, (
            "'%s' should either include a `list_test_case_class` attribute, "
            "or override the `get_list_test_case_class()` method."
            % self.__class__.__name__
        )

        return self.list_test_case_class

    def get_flow(self) -> Flow:
        list_test_case = self.get_list_test_case()
        requests_count = list_test_case.config.get("requests_count", 1)
        with Flow(self.name) as flow:
            list_data = list_test_case.map(
                range(1, requests_count + 1), unmapped(requests_count)
            )
            metrics, _ = split_test_results(list_data, mapped_=True)
            write_metrics(reduce_metrics(self.expected_metrics, flatten(metrics)))
            return flow


class BaseTestDetailScenario(BaseTestListScenario):
    detail_test_case_class: BaseDetailTestCase

    @property
    def expected_metrics(self) -> List[MetricName]:
        return [
            MetricName.AVG_RESPONSE_TIME,
            MetricName.PEAK_RESPONSE_TIME,
            MetricName.ERROR_RATE,
        ]

    def get_detail_test_case(self) -> BaseDetailTestCase:
        """
        Return the detail test case instance, the primary task of the flow.
        The configuration is expected to have a key with the same name
        of the class, that will be passed to initialize the instance.
        """
        detail_test_case_class = self.get_detail_test_case_class()
        config = self.cases.get(detail_test_case_class.__name__, {})
        return detail_test_case_class(config, self.platform)

    def get_detail_test_case_class(self) -> BaseDetailTestCase:
        """
        Return the class to use for the detail test case.
        Defaults to using `self.detail_test_case_class`.
        You may want to override this if you need to provide different
        test case class depending on other conditions.
        """
        assert self.detail_test_case_class is not None, (
            "'%s' should either include a `detail_test_case_class` attribute, "
            "or override the `get_detail_test_case_class()` method."
            % self.__class__.__name__
        )

        return self.detail_test_case_class

    def get_picking_filter(self, config: Dict) -> Callable[[Dict], bool]:
        return lambda x: True

    def get_flow(self) -> Flow:
        list_test_case = self.get_list_test_case()
        detail_test_case = self.get_detail_test_case()

        with Flow(self.name) as flow:
            list_data = list_test_case()
            _, response = split_test_results(list_data, mapped_=False)
            is_valid_response = check_response_status(response)
            is_empty_response = check_empty_response(response)
            with case(is_valid_response, True) and case(is_empty_response, False):
                requests_count = detail_test_case.config.get("requests_count", 1)
                filter_by_callback = self.get_picking_filter(detail_test_case.config)
                pks = pick_random_pks(
                    response, requests_count, filter_by=filter_by_callback
                )
                pks_count = check_length(pks)
                with case(pks_count, True):
                    detail_data = detail_test_case.map(pks)
                    metrics, _ = split_test_results(detail_data, mapped_=True)
                    write_metrics(
                        reduce_metrics(self.expected_metrics, flatten(metrics))
                    )

            with case(is_valid_response, True) and case(is_empty_response, True):
                write_metrics([])  # TODO Write errors instead

            with case(is_valid_response, False):
                write_metrics([])  # TODO Write errors instead

            return flow
