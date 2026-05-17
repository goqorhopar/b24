# Contributing to Meeting Bot

Thank you for your interest in contributing to Meeting Bot! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers and help them learn

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/meeting-bot.git`
3. Add upstream remote: `git remote add upstream https://github.com/goqorhopar/b24.git`
4. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites

- Python 3.11+
- pip
- Docker (optional, for containerized development)
- Chrome/Chromium browser

### Local Setup

```bash
# Install dependencies
make install

# Setup development environment
make dev

# Run tests
make test

# Format code
make format

# Run linters
make lint
```

### Docker Development

```bash
# Build and run with Docker
make docker-build
make docker-run

# View logs
docker-compose logs -f
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 120)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints where possible

### Code Organization

```python
# Imports order
import standard_library
import third_party
import local_modules

# Class and function structure
class ClassName:
    """Docstring with description."""
    
    def method_name(self, param: str) -> bool:
        """
        Brief description.
        
        Args:
            param: Description of parameter
            
        Returns:
            Description of return value
        """
        pass
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: fix bug
docs: update documentation
style: format code
refactor: refactor code
test: add tests
chore: update dependencies
```

## Testing

### Running Tests

```bash
# All tests
make test

# Fast tests (no coverage)
make test-fast

# Specific test file
pytest tests/test_meeting_bot.py -v

# With coverage
pytest --cov=meeting_bot --cov-report=html
```

### Writing Tests

- Write unit tests for all public functions
- Include edge cases and error conditions
- Mock external dependencies
- Aim for >80% code coverage

Example:

```python
def test_valid_url():
    bot = MeetingBot()
    assert bot.validate_url("https://meet.google.com/test") is True

def test_invalid_url():
    bot = MeetingBot()
    assert bot.validate_url("javascript:alert(1)") is False
```

## Submitting Changes

### Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Run linters and formatters
5. Update CHANGELOG.md
6. Submit PR with clear description

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted (black, isort)
- [ ] Linters pass (flake8)
- [ ] No security issues (bandit)
- [ ] Changelog updated

### Code Review

- Be patient with reviewers
- Address feedback promptly
- Ask questions if unclear
- Keep PRs small and focused

## Release Process

### Versioning

Follow [Semantic Versioning](https://semver.org/):

- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Steps

1. Update version in files
2. Update CHANGELOG.md
3. Create release branch
4. Tag release
5. Publish to PyPI (if applicable)
6. Create GitHub release

## Questions?

- Open an issue for bugs
- Use Discussions for questions
- Contact maintainers for sensitive issues

Thank you for contributing! 🎉
