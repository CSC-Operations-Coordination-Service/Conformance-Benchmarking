from typing import Any, Dict, List

from prefect import Flow, Parameter

from yasube.shared.platforms import Platform
from yasube.shared.typed_dicts import CaseConfig, GlobalConfig


class TestScenario:
    def __init__(
        self,
        key: str,
        name: str,
        cases: Dict[str, CaseConfig],
        platform: Platform,
        config: GlobalConfig,
        *args: List[Any],
        **kwargs: Dict[str, Any]
    ) -> None:
        self.key = key
        self.name = name
        self.cases = cases
        self.platform = platform
        self.config = config
        self.flow: Flow = self.get_flow()
        if self.config is not None:
            result_basepath = self.config.get("result_basepath", "~")
            result_filename = self.config.get("result_filename", "yasube_results.json")
            self.result_basepath = Parameter("result_basepath", default=result_basepath)
            self.result_filename = Parameter("result_filename", default=result_filename)

    def get_flow(self) -> Flow:
        """Implemented by subclasses"""
        pass

    def run(self, executor):
        # This will just add the Parameter to the flow.
        # It will be used later to configure the LocalResult
        # location path.
        self.flow.add_task(self.result_basepath)
        self.flow.add_task(self.result_filename)
        return self.flow.run(executor=executor)
