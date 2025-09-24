# Multi-stage build для оптимизации размера образа
FROM node:18-alpine AS base

# Установка системных зависимостей
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    ffmpeg \
    pulseaudio \
    pulseaudio-dev \
    alsa-lib \
    alsa-lib-dev \
    python3 \
    make \
    g++ \
    && rm -rf /var/cache/apk/*

# Настройка Puppeteer для работы с Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser \
    CHROME_BIN=/usr/bin/chromium-browser \
    CHROME_PATH=/usr/bin/chromium-browser

# Создание пользователя для безопасности
RUN addgroup -g 1001 -S nodejs && \
    adduser -S meetingbot -u 1001 -G nodejs

# Установка рабочей директории
WORKDIR /app

# Копирование package.json и package-lock.json
COPY package*.json ./

# Установка зависимостей
RUN npm ci --only=production && npm cache clean --force

# Копирование исходного кода
COPY --chown=meetingbot:nodejs . .

# Создание необходимых директорий
RUN mkdir -p /data/audio/raw /data/audio/processed /var/log/meetingbot /tmp && \
    chown -R meetingbot:nodejs /data /var/log/meetingbot /tmp

# Настройка PulseAudio для пользователя
RUN mkdir -p /home/meetingbot/.config/pulse && \
    chown -R meetingbot:nodejs /home/meetingbot

# Переключение на пользователя meetingbot
USER meetingbot

# Настройка переменных окружения
ENV NODE_ENV=production \
    DOCKER_MODE=true \
    DATA_DIR=/data \
    LOGS_DIR=/var/log/meetingbot \
    AUDIO_DIR=/data/audio \
    TEMP_DIR=/tmp \
    PULSEAUDIO_SINK=meeting_bot_sink \
    PULSEAUDIO_SOURCE=meeting_bot_source

# Открытие порта
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD node scripts/healthcheck.js || exit 1

# Команда запуска
CMD ["node", "src/index.js"]