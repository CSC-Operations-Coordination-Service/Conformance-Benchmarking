import logging
from typing import List, NamedTuple, Type

import prefect
from prefect.executors import LocalDaskExecutor

from yasube.shared.platforms import Platform
from yasube.shared.test_scenario import TestScenario
from yasube.shared.typed_dicts import (
    CaseConfig,
    GlobalConfig,
    PlatformConfig,
    ScenarioConfig,
)
from yasube.utils.dicts import merge_dicts
from yasube.utils.module_loading import import_string


class Execution(NamedTuple):
    scenario: ScenarioConfig
    platform: PlatformConfig


ExecutionPlan = List[Execution]


logger = logging.getLogger()


class Planner:
    """
    Class responsible for scenarios execution.
    """

    def __init__(self, execution_plan: ExecutionPlan, config: GlobalConfig):
        self.execution_plan = execution_plan
        self.config = config

    def _load_scenario(self, path: str) -> Type[TestScenario]:
        try:
            return import_string(path)
        except ImportError as exc:
            logger.error(repr(exc))

    def execute(self):
        for scenario_config, platform_config in self.execution_plan:
            scenario_class = self._load_scenario(scenario_config["path"])
            if scenario_class is None:
                msg = f"Scenario '{scenario_config['path']}' not found, skipping"
                logger.warn(msg)
                continue

            # This will prioritize possible platform specific configuration
            custom_scenario_override: ScenarioConfig = platform_config.pop(
                "scenarios", {}
            ).get(scenario_config["key"], {})
            custom_cases_config: CaseConfig = custom_scenario_override.get("cases", {})
            scenario_config["cases"] = merge_dicts(
                scenario_config["cases"], custom_cases_config
            )

            platform = Platform(**platform_config)
            scenario = scenario_class(
                scenario_config["key"],
                scenario_config["name"],
                scenario_config["cases"],
                platform,
                self.config,
            )

            # The number of workers is computed as follows:
            # - Get it from the custom scenario configuration inside the platform configuration
            # - If not present, get it from the general scenario configuration
            # - If not present, defaults to the platform setting
            workers = custom_scenario_override.get(
                "num_workers", scenario_config.get("num_workers", platform.num_workers)
            )
            logger = prefect.context.get("logger")
            logger.info(
                f"Running {scenario.name} on {platform.label} with {workers} worker(s)"
            )
            executor = LocalDaskExecutor(scheduler="threads", num_workers=workers)
            scenario.run(executor=executor)
