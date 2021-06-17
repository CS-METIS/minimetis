import time
import threading
import asyncio
from typing import Optional
from sarge import run  # type: ignore


def wait_respond(url: str, timeout: Optional[float] = None, retry_interval: float = 1):
    test = f"curl --output /dev/null -k --silent --fail {url}"
    stop_event = threading.Event()

    def test_func():
        while not stop_event.is_set() and run(test).returncode != 0:
            time.sleep(retry_interval)

    t = threading.Thread(target=test_func)
    t.start()
    t.join(timeout=timeout)
    timedout = t.is_alive()
    stop_event.set()
    if timedout:
        raise asyncio.TimeoutError(
            f"service {url} does not answer before {timeout} seconds"
        )
