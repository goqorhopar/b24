FROM node:18-alpine

# Install Python and system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    chromium \
    ffmpeg \
    curl \
    wget \
    git

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    google-generativeai \
    requests \
    python-dotenv

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs data recordings

# Set permissions
RUN chmod +x router.py

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Start the application
CMD ["node", "telegram_bot.js"]