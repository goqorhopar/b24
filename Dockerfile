# =============================================================================
# MEETING BOT - PRODUCTION DOCKERFILE
# Multi-stage build for minimal image size and security
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim-bookworm as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    gnupg \
    ca-certificates \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim-bookworm as production

LABEL maintainer="Meeting Bot Team"
LABEL version="2.1"
LABEL description="Automatic meeting bot with transcription support"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /opt/meeting-bot

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Chrome dependencies
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    # FFmpeg for recording
    ffmpeg \
    # Utilities
    curl \
    git \
    procps \
    psmisc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $2}' | cut -d'.' -f1) \
    && CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}) \
    && wget -q https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip -d /usr/local/bin/ \
    && rm chromedriver_linux64.zip \
    && chmod +x /usr/local/bin/chromedriver

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create necessary directories
RUN mkdir -p /opt/meeting-bot/recordings \
    /opt/meeting-bot/logs \
    /opt/meeting-bot/chrome-profile \
    /opt/meeting-bot/temp \
    && chown -R root:root /opt/meeting-bot \
    && chmod -R 755 /opt/meeting-bot

# Copy application code
COPY meeting-bot.py .
COPY load_auth_data.py .
COPY auth_platforms.py .
COPY simple_auth.py .
COPY quick_auth.py .
COPY monitor_bot.py .
COPY check_auth.py .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash meetingbot \
    && chown -R meetingbot:meetingbot /opt/meeting-bot

# Switch to non-root user
USER meetingbot

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["python", "meeting-bot.py"]

# Expose health check port (if needed)
EXPOSE 8080
