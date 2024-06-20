
# Benchmarking SW Test Suite v1.3.0

The Benchmarking Test Suite software addresses the performance and availability of those interfaces by performing a regular evaluation of the Ground Segment Services interfaces and comparing their results with pre-established thresholds, focusing on the operational criteria of query & download performance and availability of the interface:

* LTA: LTA Interface Point
* PRIP: Production Interface Point
* AUXIP: Auxiliary Data Interface Point
* CADIP: CADU Interface Delivery Point Specification

The Benchmarking Test Suite is an ad-hoc Python application and is deployed as a set of two applications:
* cba (Conformance Benchmark Assessment)
* yasube (Yet Another SUite for BEnchmarking)


## Download and install 
The Benchmarking SW Test Suite require Python 3.9. [Download](https://www.python.org/downloads/) and install the Python software according to your preferred operative system.
Check your installed version with
```
  > python --version
```
Create an environment:
```
  > python -m venv .env
  > .env\Scripts\activate
```
Install the apps:
```
  > python -m pip install -U ./yasube/
  > python -m pip install -U ./testsuite-ben/
```
Set environment variables:
- Windows power shell:
```
	> $env:PREFECT__FLOWS__CHECKPOINTING="true"
	> $env:PREFECT__USER_CONFIG_PATH="./testsuite-ben/cba/config/config.toml"
```
- Linux bash shell:
```
	> export PREFECT__FLOWS__CHECKPOINTING=true
	> export PREFECT__USER_CONFIG_PATH=./testsuite-ben/cba/config/config.toml
```

### Test Suite configuration

The SW Test Suite package has a config folder with a config.yaml file containing the connection parameters and credentials for each *SERVICE_PROVIDER_PLATFORM_AUTHENTICATION* quadruple.
Edit this file and change the section for the given *SERVICE_PROVIDER_PLATFORM_AUTHENTICATION*, modifying the values of the YAML array to connect to a given Interface Delivery Point.

For example, change the corresponding "yourusername", "yourpassword", "yourclientsecret" etc. with your account info in the file:
	./testsuite-ben/cba/config/config.yaml

**Please note:**
The Configuration Settings are customized for each providers in the config.yaml (e.g.: the queries for each test scenario).

### Test Suite run
 
When the configuration of the SW Test Suite is complete, the user can execute tests.
The Benchmarking Tests are organized in scenarios that simulate typical use cases. Each test scenario includes one or more test cases, orchestrated through a workflow engine.

The following table describes the provided scenarios:

| Test Scenario | Description |
| ----------- | ----------- |
| TS01 | The scenario requests a list of products. It is comprised of a single test case: TestCase001 |
| TS02 | The scenario randomly picks several products by product type and it issues detail requests using the chosen product ids. It is comprised of two test cases: TestCase001, TestCase011 | 
| TS03 | The scenario assesses the product download performance. It is comprised of two test cases: TestCase001, TestCase021 |
| TS04 | The scenario requests a list of subscriptions. It is comprised of a single test case: TestCase601 | 
| TS05 | The scenario evaluates the platform availability. It is comprised of a single test case: TestCase001 |
| TS06 | The scenario requests a list of sessions. It is comprised of a single test case: TestCase701 |
| TS07 | The scenario randomly picks several sessions by product type and it issues detail requests using the chosen product ids. It is comprised of two test cases: TestCase701, TestCase711 | 
| TS08 | The scenario assesses the file download performance. It is comprised of two test cases: TestCase801, TestCase821 |
| TS09 | The scenario requests a list of files. It is comprised of a single test case: TestCase801 |
| TS10 | The scenario randomly picks several files by product type and it issues detail requests using the chosen product ids. It is comprised of two test cases: TestCase801, TestCase811 | 

The user can choose a Test Scenario from the table and run the following command:

  >*yasube -c ./testsuite-ben/cba/config/config.yaml -s SERVICE -p SERVICE_PROVIDER_PLATFORM_AUTH TEST_SCENARIO*

After the execution, the Results are saved in the file cba_testSuiteResults.json into the folder defined in the config.yaml file (default: */tmp/*).
The following example override the defaults for the output:

  >*yasube -c ./testsuite-ben/cba/config/config.yaml -s LTA -p LTA_EXPRIVIA_S1_OAUTH TS01 --result-basepath /tmp/TS01 --result-filename ts01_lta_exprivia_s1.json*

## Usage

The full usage of the yasube app is shown by the help option of the command:
```
yasube --help
```
And the output is the following:
```
Usage: yasube [OPTIONS] [SCENARIOS]...

  Launch the benchmark suite using the provided configuration.

  A number of arguments and options can be set to limit the number of tests to
be executed.

  By default, every configured scenario will be executed on the default
  platform.

  If one or more scenarios are given, they will be executed either on the
  default platform or on the one passed in by the --platform option if
  compatible. This argument will take precedence over the --services option
  (see below).

  If one or more services are given, every tagged scenario will be executed
  either on the default platform or on the one passed in by the --platform
  option if compatible. This option is ignored if scenarios are passed in (see
  above).

  A --dryrun option is available that only prints out the execution plan and
  can be used to test a given options configuration.

Arguments:
  [SCENARIOS]...              The list of scenarios to execute. If
                              empty, the 'services' options will take
                              precedence.

Options:
  -c, --conf TEXT         The full path to the YAML configuration.  [required]
  -s, --services TEXT     The services names to run the benchmark on. If
                          empty, all the defined services or the given
                          scenarios will be executed.
  -p, --platform TEXT     The name of the platform to use, specified in the
                          YAML configuration. Will override the default one
                          set for each given scenario.
  --result-basepath TEXT  The path where the test results must be written to.
                          Override the value of the configuration file.
  --result-filename TEXT  The name of the test results file. Override the
                          value of the configuration file.
  -e, --echo              Print out the configuration and exit.
  -d, --dryrun            Do not perform any scenario, only print out the
                          execution plan.
  --help                  Show this message and exit.
```
