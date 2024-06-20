from contextlib import ContextDecorator
from timeit import default_timer as timer
from typing import Callable


class TimerError(Exception):
    pass


class Timer(ContextDecorator):
    def __init__(self, text="{:0.4f}", callback: Callable[[str or float]] = print):
        self._start_time = None
        self._elapsed = None
        self.text = text
        self.callback = callback

    @property
    def elapsed(self) -> float:
        if self._elapsed is None:
            raise TimerError("Timer not yet finished.")

        return self._elapsed

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc_info):
        self.stop()

    def start(self):
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")

        self._elapsed = None
        self._start_time = timer()

    def stop(self):
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        self._elapsed = timer() - self._start_time
        self._start_time = None

        if self.callback:
            self.callback(self.text.format(self.elapsed))

        return self.elapsed
