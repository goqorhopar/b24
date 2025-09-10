# Базовый образ Node.js
FROM node:20-alpine

# Установка системных зависимостей
RUN apk add --no-cache curl

# Создаем непривилегированного пользователя для безопасности
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Рабочая директория
WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости (только production)
RUN npm install --only=production

# Копируем исходный код
COPY src ./src

# Меняем владельца файлов
RUN chown -R nextjs:nodejs /app

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
