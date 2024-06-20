from datetime import timedelta

import prefect
from prefect import Task

from yasube.shared.platforms import Platform
from yasube.shared.typed_dicts import CaseConfig


class MaxRetryExceeded(Exception):
    def __init__(self, max_retries, original):
        self.max_retries = max_retries
        self.original = original

    def __str__(self):
        return f"Failed after {self.max_retries} attempts\nOriginal exception: {repr(self.original)}"


class TestCase(Task):
    class Meta:
        key = "Task ID"
        name = "Task Name"

    def __init__(self, config: CaseConfig, platform: Platform, **kwargs):
        self._meta = getattr(self, "Meta")
        assert hasattr(self._meta, "key")
        assert hasattr(self._meta, "name")

        if config.get("retry_delay") is not None:
            retry_delay = timedelta(seconds=config.get("retry_delay"))
        else:
            retry_delay = None

        super().__init__(
            name=self._meta.name,
            max_retries=config.get("max_retries"),
            retry_delay=retry_delay,
            **kwargs,
        )
        self.config = config
        self.platform = platform

    def get_client(self):
        raise NotImplementedError

    def reraise_until_exhausted(self, exception: Exception):
        if self.max_retries is not None:
            if prefect.context.get("task_run_count") <= self.max_retries:
                raise exception
            else:
                raise MaxRetryExceeded(self.max_retries, exception)
        else:
            raise MaxRetryExceeded(1, exception)
