# AGENTS.md

# Environment

- Package manager: `uv`.
- Check code is correct: `make check-code-pyright`.

# General guidance

- Use type hints everywhere.
- Use standard decorators, such as `override`, when appropriate.

# Testing

- Test files must be placed in the `tests` directory, mirroring the structure of the `src` directory.
- Test names must start with `test_`, be followed by a verb in present tense, and read as `The test should...`. The names mustn't include the word "should", and they must be descriptive and concise, avoiding the inclusion of the tested function whenever possible. Examples: `test_create_user`, `test_fail_when_creating_user_with_untrusted_email`, `test_ban_user_using_administrator_account`.
