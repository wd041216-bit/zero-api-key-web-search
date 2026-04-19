# Contributing to Zero-API-Key Web Search

Thank you for your interest in contributing to **Zero-API-Key Web Search**. This document outlines the process for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors. Please be constructive in your feedback and collaborative in your approach.

## Getting Started

Before contributing, please:

1. Read the [README.md](README.md) to understand the project's purpose and architecture.
2. Check the [open issues](https://github.com/wd041216-bit/zero-api-key-web-search/issues) to see if your idea or bug has already been reported.
3. For significant changes, open an issue first to discuss the proposed change before submitting a PR.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/wd041216-bit/zero-api-key-web-search.git
cd zero-api-key-web-search

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Run the test suite
python -m unittest discover -s tests -v
```

## How to Contribute

### Reporting Bugs

When reporting a bug, please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs. actual behavior
- Your Python version and OS
- Relevant error messages or logs

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- A clear description of the proposed feature
- The motivation and use case behind it
- Any relevant examples or references

### Submitting Code Changes

1. Fork the repository and create a new branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. Make your changes following the existing code style.
3. Add or update tests as appropriate.
4. Ensure all tests pass before submitting.
5. Commit your changes using [Conventional Commits](#commit-message-convention).
6. Push to your fork and open a Pull Request.

## Commit Message Convention

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification:

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation changes only |
| `style` | Code style changes (formatting, missing semicolons, etc.) |
| `refactor` | Code refactoring without feature changes or bug fixes |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks (CI, dependencies, etc.) |
| `perf` | Performance improvements |

**Examples:**

```
feat: add Bing search engine fallback
fix: handle SSL verification errors gracefully
docs: update installation instructions in README
test: add unit tests for browse_page module
chore: update CI workflow to Python 3.12
```

## Pull Request Process

1. Ensure your PR description clearly explains the problem and solution.
2. Reference any related issues using `Fixes #<issue-number>`.
3. Make sure all CI checks pass.
4. Request a review from a maintainer.
5. PRs are merged using squash merge to keep the history clean.

## Testing

```bash
# Run all tests
python -m unittest discover -s tests -v

# Run a specific test file
python -m unittest tests.test_search_web -v
```

CLI smoke tests use `tests/fixtures/fake_ddgs/` so they stay deterministic without depending on the live search backend.

When adding new features, please include:

- Unit tests for individual functions
- Integration tests for end-to-end flows where applicable
- Edge case tests for error handling

## Security

If you discover a security vulnerability, please do **not** open a public issue. Instead, contact the maintainer directly through GitHub's private vulnerability reporting feature.

---

Thank you for helping make Zero-API-Key Web Search better for everyone.
