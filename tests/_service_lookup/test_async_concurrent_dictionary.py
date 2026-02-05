import asyncio

from wirio._service_lookup._async_concurrent_dictionary import (
    AsyncConcurrentDictionary,
)

_run_count = 0


class TestConcurrentDictionary:
    async def test_get_or_add_should_not_execute_customer_code_inside_lock(
        self,
    ) -> None:
        competing_tasks = 10
        expected_value_factory_executions = competing_tasks
        dictionary = AsyncConcurrentDictionary[str, str]()

        # Customer code
        async def value_factory(value_to_print: str) -> str:
            global _run_count  # noqa: PLW0603
            _run_count += 1
            await asyncio.sleep(1)
            return value_to_print

        async def _create_value_factory(value_to_print: str) -> str:
            return await value_factory(value_to_print)

        async def print_value(value_to_print: str) -> None:
            value_found = await dictionary.get_or_add(
                "key", lambda _: _create_value_factory(value_to_print)
            )
            print(value_found)  # noqa: T201

        tasks = [print_value(f"Task {i + 1}") for i in range(competing_tasks)]
        await asyncio.gather(*tasks)

        assert _run_count == expected_value_factory_executions

    async def test_not_block_nested_operations(self) -> None:
        dictionary = AsyncConcurrentDictionary[str, str]()

        async def reentrant_value_factory(_: str) -> str:
            # The inner upsert should not deadlock the outer get_or_add call
            await dictionary.upsert("inner-key", "value")
            return "outer-value"

        value = await asyncio.wait_for(
            dictionary.get_or_add("outer-key", reentrant_value_factory),
            timeout=1.0,
        )

        assert value == "outer-value"
        assert dictionary.get("inner-key") == "value"
