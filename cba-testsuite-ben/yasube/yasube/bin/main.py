import errno
import logging
import os
import sys
from logging.config import DictConfigurator
from pickle import EMPTY_DICT
from typing import Dict, List, Optional

import typer
import urllib3
import yaml
from cerberus import Validator, schema_registry
from prefect.utilities.logging import get_logger

from yasube.shared.planner import Execution, ExecutionPlan, Planner
from yasube.shared.typed_dicts import GlobalConfig, ScenarioConfig

# Silence ssl warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Without this var, Prefect won't write LocalResults
os.environ["PREFECT__FLOWS__CHECKPOINTING"] = "true"

# ----------------------------------------------------------------
# Custom exceptions
# ----------------------------------------------------------------


class CBAException(Exception):
    pass


class ConfigurationError(CBAException):
    pass


class ConfigurationFileNotFound(ConfigurationError):
    pass


class ConfigurationNotReadable(ConfigurationError):
    pass


class ConfigurationValidationError(ConfigurationError):
    pass


class InvalidPlatformError(ConfigurationError):
    pass


class InvalidServiceError(ConfigurationError):
    pass


class ScenarioNotFound(CBAException):
    pass


class LoggingConfigurationError(CBAException):
    pass


# ----------------------------------------------------------------
# Configuration schema
# ----------------------------------------------------------------
class ExtendedValidator(Validator):
    """This class extends the default Cerberus validator by adding
    a method that validates a value against a list of valid choices
    defined by another key within the same document."""

    def _validate_allowed_from_key(self, key, field, value):
        """
        Test that `value` is within the list of values specified
        by another `key` in the document.
        If `value` is a list, check condition for all values.
        If the document[key] is a dict, then allowed values are
        the dict keys.
        The rule's arguments are validated against this schema:
            {'type': 'string'}
        """
        if self.is_child:
            document = self.root_document
        else:
            document = self.document

        if key not in document:
            self._error(field, f"Specified key '{key}' not found")
            return False

        if not isinstance(value, list):
            value = [value]

        if isinstance(document[key], dict):
            valid_values = list(document[key].keys())
        else:
            valid_values = document[key]

        if not all([v in valid_values for v in value]):
            self._error(field, f"{value} not in {valid_values}")


SCHEMA_AUTH_CREDENTIALS_BASIC = "auth_credentials_basic"
SCHEMA_AUTH_BASIC = "auth_basic"
SCHEMA_AUTH_CREDENTIALS_OAUTH = "auth_credentials_oauth"
SCHEMA_AUTH_OAUTH = "auth_oauth"
SCHEMA_CASE = "case"
SCHEMA_CASES = "cases"
SCHEMA_GLOBAL = "global"
SCHEMA_PLATFORM = "platform"
SCHEMA_SCENARIO = "scenario"

schema_registry.add(
    SCHEMA_AUTH_CREDENTIALS_BASIC,
    {
        "username": {"type": "string", "required": True},
        "password": {"type": "string", "required": True},
    },
)

schema_registry.add(
    SCHEMA_AUTH_BASIC,
    {
        "type": {"type": "string", "allowed": ["basic"]},
        "credentials": {"schema": SCHEMA_AUTH_CREDENTIALS_BASIC, "required": True},
    },
)

schema_registry.add(
    SCHEMA_AUTH_CREDENTIALS_OAUTH,
    {
        "client_id": {"type": "string", "required": True, "nullable": True},
        "client_secret": {"type": "string", "required": True, "nullable": True},
        "token_url": {"type": "string", "required": True},
        "username": {"type": "string"},
        "password": {"type": "string"},
        "grant_type": {"type": "string", "required": True},
        "scope": {"type": "string", "required": True, "nullable": True},
        "token_requires_scope": {"type": "boolean"},
    },
)

schema_registry.add(
    SCHEMA_AUTH_OAUTH,
    {
        "type": {"type": "string", "allowed": ["oauth"]},
        "credentials": {"schema": SCHEMA_AUTH_CREDENTIALS_OAUTH, "required": True},
    },
)

schema_registry.add(
    SCHEMA_CASE,
    {
        "requests_count": {"type": "integer"},
        "requests_delay": {"type": "float"},
        "requests_timeout": {"type": "float"},
        "max_retries": {"type": "integer"},
        "retry_delay": {"type": "integer"},
    },
)

schema_registry.add(
    SCHEMA_CASES,
    {
        "num_workers": {"type": "integer"},
        "cases": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "schema": SCHEMA_CASE,
                "allow_unknown": True,
            },
        },
    },
)

schema_registry.add(
    SCHEMA_GLOBAL,
    {
        "result_basepath": {"type": "string"},
        "result_filename": {"type": "string"},
    },
)

schema_registry.add(
    SCHEMA_PLATFORM,
    {
        "key": {"type": "string", "required": True},
        "label": {"type": "string", "required": True},
        "root_uri": {"type": "string", "required": True},
        "num_workers": {"type": "integer"},
        "verify_ssl": {"type": "boolean"},
        "location_trusted": {"type": "boolean"},
        "auth": {
            "oneof": [
                {"schema": SCHEMA_AUTH_BASIC},
                {"schema": SCHEMA_AUTH_OAUTH},
            ]
        },
        "scenarios": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "schema": SCHEMA_CASES,
            },
        },
    },
)

schema_registry.add(
    SCHEMA_SCENARIO,
    {
        "key": {"type": "string", "required": True},
        "name": {"type": "string", "required": True},
        "path": {"type": "string", "required": True},
        "default_platform": {"schema": SCHEMA_PLATFORM, "required": True},
        "num_workers": {"type": "integer"},
        "compatible_platforms": {
            "type": "list",
            "schema": {"type": "string"},
            "allowed_from_key": "platforms",
        },
        "services": {
            "type": "list",
            "schema": {"type": "string"},
            "allowed_from_key": "services",
        },
        "cases": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "schema": SCHEMA_CASE,
                "allow_unknown": True,
            },
        },
    },
)

schema = {
    "logging": {
        "type": "dict",  # We are not validating logging configuration
    },
    "global": {
        "schema": SCHEMA_GLOBAL,
    },
    "queries": {
        "type": "dict",
        "keysrules": {"type": "string"},
        "valuesrules": {"type": "string"},
    },
    "platforms": {
        "required": True,
        "type": "dict",
        "keysrules": {"type": "string"},
        "valuesrules": {"schema": SCHEMA_PLATFORM},
    },
    "services": {
        "required": True,
        "type": "list",
        "schema": {"type": "string"},
    },
    "scenarios": {
        "required": True,
        "type": "dict",
        "keysrules": {"type": "string"},
        "valuesrules": {"schema": SCHEMA_SCENARIO},
    },
}


# ----------------------------------------------------------------
# CLI output utilities
# ----------------------------------------------------------------
def echo_configuration(configuration: Dict) -> None:
    typer.secho("Configured platforms:", fg=typer.colors.GREEN)
    typer.secho(f' {"Platform":<32}Root URI', fg=typer.colors.YELLOW)
    for k, p in sorted(configuration["platforms"].items()):
        typer.secho(f' {k:<32}{p["root_uri"]}')

    typer.echo("")
    typer.secho("Configured scenarios:", fg=typer.colors.GREEN)
    typer.secho(
        f' {"Scenario":<32}{"Default Platform":<32}Services', fg=typer.colors.YELLOW
    )
    for k, s in sorted(configuration["scenarios"].items()):
        typer.secho(f' {k:<32}{s["default_platform"]["key"]:<32}{s["services"]}')


def echo_execution_plan(plan: ExecutionPlan) -> None:
    typer.secho("Execution plan:", fg=typer.colors.GREEN)
    typer.secho(f' {"Scenario":<32}Platforms', fg=typer.colors.YELLOW)
    for execution in plan:
        typer.secho(f' {execution.scenario["key"]:<32}{execution.platform["key"]}')


# ----------------------------------------------------------------
# Main application
# ----------------------------------------------------------------


def setup_logging(config: Dict) -> None:
    """
    Adds configured handlers to the root Prefect logger.
    To change logging level, please refer to the config/config.toml file.
    """
    try:
        # This is the Prefect root logger
        logger = get_logger()
        configurator = DictConfigurator(config)
        handlers = config.get("handlers", EMPTY_DICT)
        for name in sorted(handlers):
            # Save a possible set level to restore it later
            level = handlers[name].get("level", None)
            handler = configurator.configure_handler(handlers[name])
            # handlers[0] is the default Prefect StreamHandler.
            # Set formatter and level from it if not specified
            default_handler = logger.handlers[0]
            handler.setFormatter(default_handler.formatter)

            if level is None:
                handler.level = default_handler.level

            logger.addHandler(handler)
    except (ValueError, TypeError, AttributeError) as e:
        err = f"Logging configuration error: {e}"
        raise LoggingConfigurationError(err)


def read_yaml(file_path):
    if not os.path.isfile(file_path):
        err = f"Configuration file not found: {file_path}"
        raise ConfigurationFileNotFound(err)

    if not os.access(file_path, os.R_OK):
        err = f"Configuration file not readable: {file_path}"
        raise ConfigurationNotReadable(err)

    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def load_config(file_path: str) -> Dict:
    config: Dict = read_yaml(file_path)
    validator = ExtendedValidator(schema)

    is_valid = validator.validate(config)
    if not is_valid:
        err = f"Invalid configuration file: {validator.errors}"
        raise ConfigurationValidationError(err)

    return config


app = typer.Typer(add_completion=False)


@app.command()
def main(
    scenarios: Optional[List[str]] = typer.Argument(
        None,
        help="""
            The list of scenarios to execute.
            If empty, the 'services' options will take precedence.
        """,
    ),
    conf: str = typer.Option(
        ..., "--conf", "-c", help="The full path to the YAML configuration."
    ),
    services: Optional[List[str]] = typer.Option(
        None,
        "--services",
        "-s",
        help="""
            The services names to run the benchmark on.
            If empty, all the defined services or the given scenarios will be executed.
        """,
    ),
    platform: str = typer.Option(
        "",
        "--platform",
        "-p",
        help="""
            The name of the platform to use, specified in the YAML configuration.
            Will override the default one set for each given scenario.
        """,
    ),
    result_basepath: str = typer.Option(
        None,
        "--result-basepath",
        help="""
            The path where the test results must be written to.
            Override the value of the configuration file.
        """,
    ),
    result_filename: str = typer.Option(
        None,
        "--result-filename",
        help="""
            The name of the test results file.
            Override the value of the configuration file.
        """,
    ),
    echo: bool = typer.Option(
        False,
        "--echo",
        "-e",
        help="""
            Print out the configuration and exit.
        """,
    ),
    dryrun: bool = typer.Option(
        False,
        "--dryrun",
        "-d",
        help="""
            Do not perform any scenario, only print out the execution plan.
        """,
    ),
) -> None:
    """
    Launch the benchmark suite using the provided configuration.

    A number of arguments and options can be set to limit the number
    of tests to be executed.

    By default, every configured scenario will be executed on the
    default platform.

    If one or more scenarios are given, they will be executed either on
    the default platform or on the one passed in by the --platform option
    if compatible.
    This argument will take precedence over the --services option (see below).

    If one or more services are given, every tagged scenario will be
    executed either on the default platform or on the one passed in
    by the --platform option if compatible.
    This option is ignored if scenarios are passed in (see above).

    A --dryrun option is available that only prints out the execution plan
    and can be used to test a given options configuration.
    """

    def validate_services(configuration: Dict, services: List[str]) -> None:
        valid_services = list(configuration["services"])
        invalid_services = [i for i in services if i not in valid_services]
        if invalid_services:
            err = f"service(s) {invalid_services} not found. Valid options are {valid_services}."
            raise InvalidServiceError(err)

    def validate_platform(configuration: Dict, platform: str) -> None:
        valid_platforms = list(configuration["platforms"].keys())
        if platform and platform not in valid_platforms:
            err = f"Platform {platform} not found. Valid options are {valid_platforms}."
            raise InvalidPlatformError(err)

    def compatible_scenarios(
        scenarios: List[Dict], platform: str
    ) -> List[ScenarioConfig]:
        return [
            scenario
            for scenario in scenarios
            if platform in scenario["compatible_platforms"]
        ]

    def scenarios_from_services(
        configuration: Dict, services: List[str]
    ) -> List[ScenarioConfig]:
        scenarios: Dict[str, ScenarioConfig] = configuration["scenarios"]
        return [
            scenario
            for _, scenario in scenarios.items()
            if any([s for s in scenario["services"] if s in services])
        ]

    def scenarios_from_configuration(
        scenarios_keys: List[str], configuration: Dict
    ) -> List[ScenarioConfig]:
        scenarios: Dict[str, ScenarioConfig] = configuration["scenarios"]
        for key in scenarios_keys:
            if key not in scenarios.keys():
                raise ScenarioNotFound(f"Scenario {key} not found.")

        return [
            scenario for key, scenario in scenarios.items() if key in scenarios_keys
        ]

    try:
        configuration = load_config(conf)
        validate_services(configuration, services)
        validate_platform(configuration, platform)

        if echo:
            echo_configuration(configuration)
            sys.exit()

        if scenarios:
            scenarios = scenarios_from_configuration(scenarios, configuration)

        if not scenarios and services:
            scenarios: List[ScenarioConfig] = scenarios_from_services(
                configuration, services
            )

        if platform:
            scenarios: List[ScenarioConfig] = compatible_scenarios(scenarios, platform)
            execution_plan = [
                Execution(scenario, configuration["platforms"][platform])
                for scenario in scenarios
            ]
        else:
            execution_plan = [
                Execution(scenario, scenario["default_platform"])
                for scenario in scenarios
            ]

        if dryrun:
            echo_execution_plan(execution_plan)
            sys.exit()

        custom_logging = configuration.get("logging")
        if custom_logging is not None:
            setup_logging(custom_logging)

        global_config: GlobalConfig = configuration.get(SCHEMA_GLOBAL, {})
        if result_basepath is not None:
            global_config["result_basepath"] = result_basepath
        if result_filename is not None:
            global_config["result_filename"] = result_filename

        planner = Planner(execution_plan, global_config)
        planner.execute()

    except ConfigurationFileNotFound as e:
        logging.error(e)
        raise typer.Exit(errno.ENOENT)
    except LoggingConfigurationError as e:
        logging.error(e)
        raise typer.Exit(errno.EINVAL)
    except Exception as e:
        logging.error(repr(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
