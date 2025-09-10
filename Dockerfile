# Базовый образ Node.js на Alpine (минимальный размер)
FROM node:20-alpine AS builder

# Установка системных зависимостей для сборки
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    curl

# Рабочая директория
WORKDIR /app

# Копируем package.json и package-lock.json для установки зависимостей
COPY package*.json ./

# Устанавливаем все зависимости (включая dev для сборки)
RUN npm ci --include=dev

# Копируем исходный код
COPY . .

# Сборка приложения (если требуется)
RUN npm run build --if-present

# Удаляем dev зависимости после сборки
RUN npm prune --production

# Финальный образ
FROM node:20-alpine AS runtime

# Устанавливаем зависимости для здоровья приложения
RUN apk add --no-cache curl

# Создаем непривилегированного пользователя для безопасности
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Рабочая директория
WORKDIR /app

# Копируем установленные зависимости из builder
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

# Копируем собранное приложение и исходный код
COPY --from=builder --chown=nextjs:nodejs /app/src ./src
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

# Переключаемся на непривилегированного пользователя
USER nextjs

# Переменные окружения
ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Открываем порт
EXPOSE 3000

# Healthcheck для мониторинга состояния приложения
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Команда запуска приложения
CMD ["node", "src/index.js"]
