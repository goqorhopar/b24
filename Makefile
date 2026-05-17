# =============================================================================
# MEETING BOT - MAKEFILE
# Common development and deployment tasks
# =============================================================================

.PHONY: help install dev test lint format clean build docker-build docker-run deploy

# Default target
help:
@echo "Meeting Bot - Available Commands"
@echo "================================="
@echo ""
@echo "Development:"
@echo "  make install       - Install all dependencies"
@echo "  make dev           - Install dev dependencies and setup pre-commit"
@echo "  make test          - Run tests with coverage"
@echo "  make test-fast     - Run tests without coverage"
@echo "  make lint          - Run all linters"
@echo "  make format        - Format code with black and isort"
@echo "  make type-check    - Run mypy type checking"
@echo "  make security      - Run security checks"
@echo ""
@echo "Docker:"
@echo "  make docker-build  - Build Docker image"
@echo "  make docker-run    - Run Docker container"
@echo "  make docker-stop   - Stop Docker container"
@echo "  make docker-clean  - Remove Docker containers and images"
@echo ""
@echo "Deployment:"
@echo "  make deploy        - Deploy to production (requires config)"
@echo "  make backup        - Backup auth data and recordings"
@echo "  make restore       - Restore from backup"
@echo ""
@echo "Maintenance:"
@echo "  make clean         - Clean build artifacts and cache"
@echo "  make logs          - View bot logs"
@echo "  make status        - Check bot status"
@echo ""

# Install dependencies
install:
pip install -r requirements.txt

# Development setup
dev: install
pre-commit install
pip install pytest pytest-asyncio pytest-cov black flake8 isort mypy bandit

# Run tests
test:
pytest --cov=meeting_bot --cov-report=term-missing --cov-report=html

test-fast:
pytest -v --tb=short

# Linting
lint:
flake8 meeting-bot.py tests/
isort --check-only meeting-bot.py tests/
black --check meeting-bot.py tests/

# Format code
format:
isort meeting-bot.py tests/
black --line-length=120 meeting-bot.py tests/

# Type checking
type-check:
mypy meeting-bot.py --ignore-missing-imports

# Security checks
security:
bandit -r meeting-bot.py -ll
python -m pip check

# Docker commands
docker-build:
docker build -t meeting-bot:latest .

docker-run:
docker-compose up -d

docker-stop:
docker-compose down

docker-clean:
docker-compose down -v
docker rmi meeting-bot:latest || true

# Deployment
deploy:
@echo "Deploying Meeting Bot..."
@echo "Please configure your deployment settings first"

# Backup
backup:
@echo "Creating backup..."
mkdir -p backups
tar -czf backups/meeting-bot-backup-$$(date +%Y%m%d-%H%M%S).tar.gz \
recordings/ auth_data/ .env 2>/dev/null || echo "Some files may not exist"
@echo "Backup created in backups/"

# Restore
restore:
@echo "Restoring from backup..."
@echo "Please specify backup file: make restore BACKUP_FILE=backups/backup.tar.gz"

# Clean
clean:
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name "*.egg-info" -exec rm -rf {} +
rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ htmlcov/ coverage.xml
rm -rf .coverage coverage_report/
@echo "Cleaned build artifacts"

# Logs
logs:
tail -f logs/meeting-bot.log 2>/dev/null || echo "No log file found"

# Status
status:
ps aux | grep meeting-bot | grep -v grep || echo "Bot is not running"
systemctl status meeting-bot 2>/dev/null || echo "Systemd service not found"

# Health check
health:
curl -f http://localhost:8080/health || echo "Health check failed or endpoint not available"
