import os
from datetime import datetime
from random import choices, sample
from typing import Callable, Dict, List, Tuple, Union

import prefect
from prefect import task
from prefect.engine.results import LocalResult
from prefect.engine.serializers import JSONSerializer
from requests import Response

from yasube.shared.metrics import Metric, MetricName
from yasube.shared.reducers import MetricReducer
from yasube.utils.strings import camel_to_snake

FilterFunc = Callable[[Dict], bool]


def format_location(date, result_basepath, result_filename, task_name, **kwargs):
    # Notice we expand the user at runtime so the user of the parameter
    # does not need to worry about the path to the home directory on the
    # server that the flow runs on
    # TODO We might support templating from the YAML file to inject running time
    # variables into the final path
    return f"{os.path.join(os.path.expanduser(result_basepath), result_filename)}"


@task
def check_response_status(response: Response, status_code: int = 200) -> bool:
    """Returns True or False whether the response status code matches the argument."""
    return response is not None and response.status_code == status_code


@task
def check_empty_response(response: Response, items_key: str = "value") -> bool:
    """Returns True or False whether the response bears no results."""
    return response is not None and not bool(response.json().get(items_key))


@task
def check_length(iterable: List) -> bool:
    return bool(len(iterable))


@task
def pick_random_pks(
    response: Response,
    count: int = 1,
    items_key: str = "value",
    pk_key: str = "Id",
    filter_by: FilterFunc = None,
) -> List[Union[str, int]]:
    """Given a valid Response object, returns a `count` number of primary keys
    taken from the payload.
    The list of items are expected to be defined by the `items_key` parameter,
    while the primary key is the `pk_key` one.
    If the number of items is less the the number of expected results, there
    will be repetions, otherwise the primary keys will be unique.
    """
    # We can assume response status code is 200
    items = response.json()[items_key]
    if filter_by is None:
        filter_by = lambda x: True
    pks = [i[pk_key] for i in items if filter_by(i)]
    if len(pks) >= count:
        return sample(pks, count)
    if len(pks) == 0:
        return []
    return choices(pks, k=count)


@task
def split_test_results(
    data: Tuple[List[Metric], Response], mapped_: bool
) -> Tuple[List[Metric], Response]:
    """Returns a tuple with the list of metrics and a response.
    If `data` comes from a mapped task, the metrics will be returned unflattened, and
    the response will be the last of the batch.
    """
    if mapped_:
        return [d[0] for d in data], data[-1][1]
    return data[0], data[1]


@task(
    result=LocalResult(location=format_location, serializer=JSONSerializer()),
)
def write_metrics(metrics: List[Metric]):
    """Writes the output."""
    start_date = prefect.context.date
    end_date = datetime.utcnow().replace(tzinfo=start_date.tzinfo)
    duration = round((end_date - start_date).total_seconds(), 2)
    return {
        "testResults": [
            {
                "testName": prefect.context.flow_name,
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "duration": duration,
                "metrics": [m.to_json() for m in metrics],
            }
        ],
    }


@task
def reduce_metrics(
    expected_metrics: List[MetricName], test_metrics: List[Metric]
) -> List[Metric]:
    """Returns a list of Metric objects by reducing the given `test_metrics`,
    following the `expected_metrics`.
    Typically those will involve average, peak or total values.
    Each expected metric is expected to have a correspondant implementation
    method in the MetricReducer class.
    """
    results = []
    for metric in expected_metrics:
        metric_name = camel_to_snake(metric.value)
        try:
            method = getattr(MetricReducer, f"reduce_{metric_name}")
            results.append(method(test_metrics))
        except AttributeError:
            logger = prefect.context.get("logger")
            logger.warning(f"No reducer implemented for metric {metric.name}")

    return results
