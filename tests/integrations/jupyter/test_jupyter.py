import json
import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    os.environ.get("CI") is None,
    reason="Slow tests",
)
class TestJupyter:
    def test_service_collection_usage(self) -> None:
        current_path = Path(__file__).parent.resolve()
        notebook = current_path / "service_collection_usage.ipynb"

        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "uv",
                "run",
                "jupyter",
                "execute",
                "--timeout=10",
                str(notebook),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr

    def test_get_content_root_path_with_services_defined_in_notebook(self) -> None:
        current_path = Path(__file__).parent.resolve()
        expected_content_root_path = str(current_path)
        notebook = (
            current_path
            / "get_content_root_path_with_services_defined_in_notebook.ipynb"
        )

        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "uv",
                "run",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--stdout",
                "--ExecutePreprocessor.timeout=10",
                str(notebook),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr

        output = json.loads(result.stdout)["cells"][1]["outputs"][0]["text"][0].strip()
        assert output == expected_content_root_path

    def test_get_content_root_path_with_services_defined_in_another_file(self) -> None:
        expected_content_root_path = str((Path.cwd() / "tests/utils").resolve())
        current_path = Path(__file__).parent.resolve()
        notebook = (
            current_path
            / "get_content_root_path_with_services_defined_in_another_file.ipynb"
        )

        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "uv",
                "run",
                "jupyter",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--stdout",
                "--ExecutePreprocessor.timeout=10",
                str(notebook),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr

        output = json.loads(result.stdout)["cells"][3]["outputs"][0]["text"][0].strip()
        assert output == str(expected_content_root_path)
