# CI/CD Setup Design for or-algo

**Date:** 2026-07-29
**Status:** Approved
**Reference:** `or-register` package (D:\github\register)

## Overview

Migrate `or-algo` from Poetry to uv/hatchling and add GitHub Actions CI/CD workflows, following the patterns established in the `or-register` package.

## Changes

### 1. `pyproject.toml` — Poetry → hatchling

Replace the Poetry-based configuration with hatchling (PEP 621 compliant) for uv compatibility.

#### Build System

```toml
[build-system]
requires = ["hatchling>=1.20.0"]
build-backend = "hatchling.build"
```

#### Project Metadata

```toml
[project]
name = "or-algo"
version = "0.2.0"
description = "A general-purpose algorithm framework for orchestrating solvers"
authors = [{name = "Hermin-Yakovski", email = "hemin.ye@qq.com"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "ortools>=9.15.6755",
    "or-register>=0.2.0",
]
```

#### Dev Dependencies

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.8",
    "mypy>=1.10",
    "pytest-cov>=7.1.0",
]
```

#### Hatch Build Target

```toml
[tool.hatch.build.targets.wheel]
packages = ["or_algo"]
```

#### Coverage Config

```toml
[tool.coverage.run]
source = ["or_algo"]
```

#### Pytest Config

```toml
[tool.pytest.ini_options]
addopts = "--cov --cov-report=term-missing --cov-report=html"
```

#### Tool Config (Keep Existing)

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
exclude = ["tests/"]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "ortools.*"
ignore_missing_imports = true
```

**Removed:**
- `[tool.poetry]` and all poetry-specific sections
- `[tool.poetry.dependencies]`
- `[tool.poetry.group.dev.dependencies]`
- `[tool.ruff] exclude = ["tests"]` (match register pattern)
- `[tool.mypy.overrides]` for `register` module (now `or-register` with proper stubs)

### 2. `.python-version` — New File

```
3.11
```

Pins the Python version for uv.

### 3. `.github/workflows/ci.yml` — New File

Triggers on pull requests to `main`. Runs lint, format check, type check, tests, and build.

```yaml
name: CI

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  ci:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Install dependencies
        run: uv sync

      - name: Lint
        run: uv run ruff check

      - name: Format check
        run: uv run ruff format --check

      - name: Type check
        run: uv run mypy or_algo/

      - name: Test
        run: uv run pytest

      - name: Upload HTML coverage report
        uses: actions/upload-artifact@v4
        with:
          name: html-coverage-report
          path: htmlcov/

      - name: Build
        run: uv build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-packages
          path: dist/
```

### 4. `.github/workflows/cd.yml` — New File

Triggers on version tags (`v*`). Builds and publishes to TestPyPI.

```yaml
name: CD

on:
  push:
    tags: ["v*"]

permissions:
  contents: read

jobs:
  publish-testpypi:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Build
        run: uv build

      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          repository-url: https://test.pypi.org/legacy/
          password: ${{ secrets.TEST_PYPI_API_TOKEN }}
```

### 5. Cleanup

- **Delete:** `poetry.lock` (superseded by `uv.lock` generated on first `uv sync`)
- **Delete:** `dist/` directory (old poetry build artifacts, if present)
- **Add to `.gitignore`:** `poetry.lock`, `poetry.toml` (defensive, in case Poetry is invoked accidentally)

## Dependencies

- **or-register**: Published on PyPI (>=0.2.0)
- **ortools**: Google OR-Tools (>=9.15.6755)

## Testing

After implementation:
1. Run `uv sync` to generate `uv.lock`
2. Run `uv run ruff check` — lint passes
3. Run `uv run ruff format --check` — format passes
4. Run `uv run mypy or_algo/` — type check passes
5. Run `uv run pytest` — tests pass
6. Run `uv build` — produces `dist/or_algo-0.2.0-py3-none-any.whl` and `.tar.gz`
