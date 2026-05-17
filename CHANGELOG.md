# Changelog

All notable changes to Meeting Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- URL validation with security checks (XSS, SQL injection, path traversal prevention)
- Comprehensive test suite with unit, integration, and edge case tests
- Docker support with multi-stage build for production deployment
- docker-compose.yml for easy local development and deployment
- Makefile with common development and deployment commands
- Pre-commit hooks for code quality automation
- CI/CD pipeline with GitHub Actions
- CONTRIBUTING.md guide for contributors
- .env.example with comprehensive configuration documentation
- pytest.ini and setup.cfg for test and lint configuration
- .gitignore with proper exclusions for sensitive files

### Changed
- Fixed duplicate import statements (PEP 8 compliance)
- Moved all imports to top of file
- Improved error handling in driver cleanup
- Enhanced logging with better error messages
- Updated requirements.txt with pinned versions for reproducibility

### Fixed
- WebDriverException import error
- Memory leaks in Chrome profile cleanup
- Duplicate subprocess/shutil imports inside functions

### Security
- Added URL sanitization before processing
- Protected against XSS attacks via meeting URLs
- Protected against SQL injection attempts
- Protected against path traversal attacks
- Added secret detection in pre-commit hooks
- Enhanced .gitignore to exclude sensitive auth files

## [2.1.0] - 2024-01-15

### Added
- Support for Microsoft Teams
- Automatic authentication for all platforms
- Recording transcription with Whisper AI
- Telegram bot interface
- GitHub integration for archiving

### Changed
- Increased page load timeout for reliability
- Improved Chrome driver initialization with retries
- Enhanced error messages and logging

### Fixed
- Chrome crash handling with automatic recovery
- Session management issues
- Memory pressure problems in long meetings

## [2.0.0] - 2023-12-01

### Added
- Multi-platform support (Google Meet, Zoom, Yandex, Contour)
- Headless mode for VPS deployment
- Systemd service files
- Installation scripts

### Changed
- Major refactoring for modularity
- Improved meeting detection logic

## [1.0.0] - 2023-10-01

### Added
- Initial release
- Basic Google Meet support
- Simple recording functionality
