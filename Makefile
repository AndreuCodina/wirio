.PHONY: check-code
check-code:
	uv run -- ruff check
	uv run -- ruff format --diff
	uv run -- ty check

.PHONY: check-code-pyright
check-code-pyright:
	uv run -- ruff check
	uv run -- ruff format --diff
	uv run -- pyright

.PHONY: serve-documentation
serve-documentation:
	uv run -- mkdocs serve --config-file docs/mkdocs.yml --strict --livereload