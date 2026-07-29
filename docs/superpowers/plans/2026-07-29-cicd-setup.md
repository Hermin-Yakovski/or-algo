# CI/CD Setup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate or-algo from Poetry to uv/hatchling and add GitHub Actions CI/CD workflows.

**Architecture:** Direct pattern lift from the `or-register` package. Replace Poetry build system with hatchling, add `.python-version` for uv, add `ci.yml` (PR checks) and `cd.yml` (tag-triggered TestPyPI publish), clean up Poetry artifacts.

**Tech Stack:** uv, hatchling, GitHub Actions, PyPI

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Rewrite | Project metadata, build system, tool config |
| `.python-version` | Create | Pin Python 3.11 for uv |
| `.github/workflows/ci.yml` | Create | PR checks: lint, format, type check, test, build |
| `.github/workflows/cd.yml` | Create | Tag-triggered publish to TestPyPI |
| `.gitignore` | Modify | Add poetry.lock, poetry.toml |
| `poetry.lock` | Delete | Superseded by uv.lock |
| `dist/` | Delete | Old poetry build artifacts |

---

### Task 1: Rewrite pyproject.toml

**Files:**
- Modify: `pyproject.toml` (full rewrite)

- [ ] **Step 1: Replace entire pyproject.toml with hatchling config**

Write the complete file:

```toml
[build-system]
requires = ["hatchling>=1.20.0"]
build-backend = "hatchling.build"

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

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff>=0.8",
    "mypy>=1.10",
    "pytest-cov>=7.1.0",
]

[tool.hatch.build.targets.wheel]
packages = ["or_algo"]

[tool.coverage.run]
source = ["or_algo"]

[tool.pytest.ini_options]
addopts = "--cov --cov-report=term-missing --cov-report=html"

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

- [ ] **Step 2: Commit**

```bash
git add pyproject.toml
git commit -m "build: migrate from poetry to hatchling/uv"
```

---

### Task 2: Add .python-version

**Files:**
- Create: `.python-version`

- [ ] **Step 1: Create .python-version**

```
3.11
```

- [ ] **Step 2: Commit**

```bash
git add .python-version
git commit -m "build: add .python-version for uv"
```

---

### Task 3: Add CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create .github/workflows directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create ci.yml**

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

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add CI workflow for PR checks"
```

---

### Task 4: Add CD workflow

**Files:**
- Create: `.github/workflows/cd.yml`

- [ ] **Step 1: Create cd.yml**

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

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/cd.yml
git commit -m "ci: add CD workflow for TestPyPI publishing"
```

---

### Task 5: Cleanup Poetry artifacts and update .gitignore

**Files:**
- Delete: `poetry.lock`
- Delete: `dist/` (directory)
- Modify: `.gitignore`

- [ ] **Step 1: Delete poetry.lock**

```bash
git rm poetry.lock
```

- [ ] **Step 2: Delete dist/ directory**

```bash
git rm -r dist/
```

- [ ] **Step 3: Update .gitignore**

Append these lines at the end of `.gitignore`:

```
# Poetry
poetry.lock
poetry.toml
```

- [ ] **Step 4: Commit**

```bash
git add .gitignore
git commit -m "chore: remove poetry artifacts, update .gitignore"
```

---

### Task 6: Verify with uv

**Files:** None (verification only)

- [ ] **Step 1: Generate uv.lock**

```bash
uv sync
```

Expected: `uv.lock` is created, `.venv` is populated.

- [ ] **Step 2: Run lint**

```bash
uv run ruff check
```

Expected: `All checks passed!`

- [ ] **Step 3: Run format check**

```bash
uv run ruff format --check
```

Expected: `N files already formatted` (no changes needed).

- [ ] **Step 4: Run type check**

```bash
uv run mypy or_algo/
```

Expected: `Success: no issues found in N source files`

- [ ] **Step 5: Run tests**

```bash
uv run pytest
```

Expected: All tests pass. Coverage report generated in `htmlcov/`.

- [ ] **Step 6: Build package**

```bash
uv build
```

Expected: `dist/or_algo-0.2.0-py3-none-any.whl` and `dist/or_algo-0.2.0.tar.gz` created.

- [ ] **Step 7: Commit uv.lock**

```bash
git add uv.lock
git commit -m "chore: add uv.lock"
```
