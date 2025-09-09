# Базовый образ Node.js
FROM node:20-slim

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости (отдельно для оптимизации кеша)
COPY package*.json ./
RUN npm install --only=production

# Копируем исходники
COPY src ./src

# Переменные окружения (все подтягиваются из Render или docker-compose)
ENV NODE_ENV=production

# Запуск бота
CMD ["node", "src/index.js"]
