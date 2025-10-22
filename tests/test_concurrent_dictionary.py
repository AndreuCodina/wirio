import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from aspy_dependency_injection._concurrent_dictionary import ConcurrentDictionary

_run_count = 0


class TestConcurrentDictionary:
    async def test_get_or_add_should_execute_value_factory_only_once(
        self,
    ) -> None:
        expected_value_factory_executions = 1
        competing_tasks = 10
        dictionary = ConcurrentDictionary[str, str]()

        def value_factory(value_to_print: str) -> str:
            global _run_count  # noqa: PLW0603
            _run_count += 1
            time.sleep(1)
            return value_to_print

        def print_value(value_to_print: str) -> None:
            value_found = dictionary.get_or_add(
                "key", lambda _: value_factory(value_to_print)
            )
            print(value_found)  # noqa: T201

        event_loop = asyncio.get_running_loop()

        with ThreadPoolExecutor(max_workers=competing_tasks) as thread_pool_executor:
            tasks = [
                event_loop.run_in_executor(
                    thread_pool_executor, print_value, f"Task {i + 1}"
                )
                for i in range(competing_tasks)
            ]
            await asyncio.gather(*tasks)

        assert _run_count == expected_value_factory_executions
