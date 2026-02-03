import subprocess
from pathlib import Path


class TestJupyter:
    def test_execute_notebook(self) -> None:
        current_path = Path(__file__).parent.resolve()
        notebook = current_path / "notebook.ipynb"

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
