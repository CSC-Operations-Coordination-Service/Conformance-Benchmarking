from typing import Dict, List, TypedDict
from typing_extensions import NotRequired


class GlobalConfig(TypedDict):
    result_basepath: str
    result_filename: str


class CaseConfig(TypedDict):
    requests_count: int
    requests_delay: float
    requests_timeout: float
    max_retries: int
    retry_delay: int


class PlatformConfig(TypedDict):
    key: str
    label: str
    root_uri: str
    num_workers: int
    verify_ssl: bool
    location_trusted: NotRequired[bool]
    compatible_platforms: List[str]
    auth: dict
    scenarios: Dict[str, CaseConfig]


class ScenarioConfig(TypedDict):
    key: str
    name: str
    path: str
    num_workers: NotRequired[int]
    default_platform: PlatformConfig
    compatible_platforms: List[str]
    services: List[str]
    cases: Dict[str, CaseConfig]
