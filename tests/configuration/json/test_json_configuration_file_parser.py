import json
import re
from pathlib import Path

import pytest

from wirio.configuration.json.json_configuration_file_parser import (
    JsonConfigurationFileParser,
)
from wirio.configuration.json.json_configuration_provider import (
    JsonConfigurationProvider,
)


class TestJsonConfigurationFileParser:
    def test_parse_scalar_values(self) -> None:
        parser = JsonConfigurationFileParser()

        result = parser.parse_json(
            {
                "name": "wirio",
                "port": 8080,
                "enabled": True,
                "notes": None,
            }
        )

        assert result == {
            "name": "wirio",
            "port": "8080",
            "enabled": "True",
            "notes": None,
        }

    def test_parse_nested_objects_and_arrays(self) -> None:
        parser = JsonConfigurationFileParser()

        result = parser.parse_json(
            {
                "Logging": {"LogLevel": {"Default": "Information"}},
                "AllowedHosts": ["localhost", "example.com"],
            }
        )

        assert result == {
            "Logging:LogLevel:Default": "Information",
            "AllowedHosts:0": "localhost",
            "AllowedHosts:1": "example.com",
        }

    def test_set_null_and_empty_for_empty_structures(self) -> None:
        parser = JsonConfigurationFileParser()

        result = parser.parse_json(
            {
                "Section": {},
                "Items": [],
                "Nested": {"Child": {}},
            }
        )

        assert result == {
            "Section": None,
            "Items": "",
            "Nested:Child": None,
        }

    def test_fail_when_duplicate_key_is_found_ignoring_case(self) -> None:
        parser = JsonConfigurationFileParser()

        with pytest.raises(
            RuntimeError,
            match=re.escape("A duplicate key 'key' was found"),
        ):
            parser.parse_json({"Key": "value", "key": "other"})

    async def test_fail_when_json_file_has_invalid_syntax(self, tmp_path: Path) -> None:
        file_path = tmp_path / "appsettings.json"
        file_path.write_text('{"appName": "wirio"', encoding="utf-8")
        provider = JsonConfigurationProvider(path=file_path, optional=False)

        with pytest.raises(json.JSONDecodeError):
            await provider.load()

    async def test_fail_when_json_root_value_is_not_object(
        self, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "appsettings.json"
        file_path.write_text('["wirio", "config"]', encoding="utf-8")
        provider = JsonConfigurationProvider(path=file_path, optional=False)

        with pytest.raises(
            RuntimeError,
            match=re.escape("Could not parse the JSON file"),
        ):
            await provider.load()
