# Contributing

## Setup

```bash
git clone https://github.com/n2solutionsio/photo-sync.git
cd photo-sync
pip install -e ".[dev]"
pre-commit install
```

## Development

- Run linting: `ruff check src/ tests/`
- Run formatting: `ruff format src/ tests/`
- Run type checking: `mypy src/`
- Run tests: `pytest`

## Adding a Provider

1. Create a new file in `src/photo_sync/providers/`
2. Implement the `PhotoProvider` abstract class from `photo_sync.provider`
3. Add tests in `tests/`
4. Update the CLI to support the new provider

## Pull Requests

- Keep changes focused and small
- Add tests for new functionality
- Ensure `ruff check`, `mypy`, and `pytest` all pass
