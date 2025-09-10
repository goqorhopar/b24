#!/bin/bash

# ==========================================
# СКРИПТ АВТОДЕПЛОЯ TELEGRAM GEMINI BOT
# ==========================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Проверка git
    if ! command -v git &> /dev/null; then
        log_error "Git не установлен"
        exit 1
    fi
    
    # Проверка python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 не установлен"
        exit 1
    fi
    
    # Проверка pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 не установлен"
        exit 1
    fi
    
    log_success "Все зависимости установлены"
}

# Проверка переменных окружения
check_env_vars() {
    log_info "Проверка переменных окружения..."
    
    required_vars=(
        "TELEGRAM_BOT_TOKEN"
        "GEMINI_API_KEY"
        "RENDER_EXTERNAL_URL"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Отсутствуют обязательные переменные окружения:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_warning "Создайте .env файл или установите переменные"
        exit 1
    fi
    
    log_success "Переменные окружения проверены"
}

# Загрузка переменных из .env файла
load_env() {
    if [[ -f .env ]]; then
        log_info "Загрузка переменных из .env файла..."
        export $(grep -v '^#' .env | xargs)
        log_success "Переменные загружены"
    else
        log_warning ".env файл не найден"
    fi
}

# Установка зависимостей
install_dependencies() {
    log_info "Установка Python зависимостей..."
    
    # Создание виртуального окружения если нет
    if [[ ! -d "venv" ]]; then
        log_info "Создание виртуального окружения..."
        python3 -m venv venv
    fi
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Обновление pip
    pip install --upgrade pip
    
    # Установка зависимостей
    pip install -r requirements.txt
    
    log_success "Зависимости установлены"
}

# Инициализация базы данных
init_database() {
    log_info "Инициализация базы данных..."
    
    python3 -c "
from db import init_db
try:
    init_db()
    print('База данных инициализирована успешно')
except Exception as e:
    print(f'Ошибка инициализации БД: {e}')
    exit(1)
"
    
    log_success "База данных готова"
}

# Тестирование соединений
test_connections() {
    log_info "Тестирование соединений..."
    
    # Тест Gemini
    python3 -c "
from gemini_client import test_gemini_connection
if test_gemini_connection():
    print('✅ Gemini API работает')
else:
    print('❌ Ошибка соединения с Gemini API')
    exit(1)
" || {
        log_error "Gemini API недоступен"
        exit 1
    }
    
    # Тест Bitrix (если настроен)
    if [[ -n "$BITRIX_WEBHOOK_URL" ]]; then
        python3 -c "
from bitrix import test_bitrix_connection
if test_bitrix_connection():
    print('✅ Bitrix24 API работает')
else:
    print('⚠️ Bitrix24 API недоступен (не критично)')
" || log_warning "Bitrix24 API недоступен"
    else
        log_warning "BITRIX_WEBHOOK_URL не настроен"
    fi
    
    log_success "Тесты соединений завершены"
}

# Запуск приложения локально
run_locally() {
    log_info "Запуск приложения локально..."
    
    # Активация виртуального окружения
    source venv/bin/activate
    
    # Запуск
    python3 main.py
}

# Подготовка к деплою на Render
prepare_render_deploy() {
    log_info "Подготовка к деплою на Render..."
    
    # Проверка наличия render.yaml
    if [[ ! -f "render.yaml" ]]; then
        log_error "render.yaml не найден"
        exit 1
    fi
    
    # Проверка наличия Procfile
    if [[ ! -f "Procfile" ]]; then
        log_warning "Procfile не найден, создаю..."
        echo "web: gunicorn main:app --bind 0.0.0.0:\$PORT --workers 2 --timeout 120" > Procfile
    fi
    
    # Проверка requirements.txt
    if [[ ! -f "requirements.txt" ]]; then
        log_error "requirements.txt не найден"
        exit 1
    fi
    
    log_success "Подготовка к Render деплою завершена"
}

# Git операции
git_operations() {
    log_info "Git операции..."
    
    # Проверка статуса git
    if [[ $(git status --porcelain) ]]; then
        log_info "Обнаружены изменения, добавляю в git..."
        
        git add .
        
        echo -n "Введите сообщение коммита (или нажмите Enter для автосообщения): "
        read commit_message
        
        if [[ -z "$commit_message" ]]; then
            commit_message="Auto deploy $(date '+%Y-%m-%d %H:%M:%S')"
        fi
        
        git commit -m "$commit_message"
        log_success "Изменения зафиксированы"
    else
        log_info "Нет изменений для коммита"
    fi
    
    # Push если есть remote
    if git remote get-url origin &> /dev/null; then
        log_info "Отправка изменений в удаленный репозиторий..."
        git push origin main
        log_success "Изменения отправлены"
    else
        log_warning "Удаленный репозиторий не настроен"
    fi
}

# Отображение инструкций по настройке Render
show_render_instructions() {
    log_info "Инструкции по настройке Render:"
    echo ""
    echo "1. Зайдите на https://render.com и создайте аккаунт"
    echo "2. Подключите ваш GitHub репозиторий"
    echo "3. Создайте новый Web Service"
    echo "4. Используйте следующие настройки:"
    echo ""
    echo "   Build Command:"
    echo "   pip install --upgrade pip && pip install -r requirements.txt"
    echo ""
    echo "   Start Command:"
    echo "   gunicorn main:app --bind 0.0.0.0:\$PORT --workers 2 --timeout 120"
    echo ""
    echo "5. Добавьте переменные окружения:"
    for var in TELEGRAM_BOT_TOKEN GEMINI_API_KEY RENDER_EXTERNAL_URL BITRIX_WEBHOOK_URL ADMIN_CHAT_ID; do
        if [[ -n "${!var}" ]]; then
            echo "   $var = ${!var}"
        fi
    done
    echo ""
    echo "6. Сохраните и задеплойте!"
    echo ""
}

# Health check после деплоя
health_check() {
    if [[ -n "$RENDER_EXTERNAL_URL" ]]; then
        log_info "Проверка здоровья приложения..."
        
        sleep 30  # Ждем запуска приложения
        
        response=$(curl -s -o /dev/null -w "%{http_code}" "$RENDER_EXTERNAL_URL/health" || echo "000")
        
        if [[ "$response" == "200" ]]; then
            log_success "Приложение работает корректно!"
        else
            log_warning "Не удалось проверить здоровье приложения (код: $response)"
        fi
    fi
}

# Основная функция
main() {
    echo ""
    echo "========================================"
    echo "  TELEGRAM GEMINI BOT - АВТОДЕПЛОЙ"
    echo "========================================"
    echo ""
    
    # Загрузка переменных окружения
    load_env
    
    # Выбор режима
    echo "Выберите режим деплоя:"
    echo "1) Локальная разработка"
    echo "2) Подготовка к деплою на Render"
    echo "3) Полный цикл (проверка + git + инструкции)"
    echo ""
    echo -n "Введите номер (1-3): "
    read mode
    
    case $mode in
        1)
            log_info "Режим: Локальная разработка"
            check_dependencies
            install_dependencies
            init_database
            test_connections
            run_locally
            ;;
        2)
            log_info "Режим: Подготовка к Render деплою"
            check_dependencies
            check_env_vars
            prepare_render_deploy
            git_operations
            show_render_instructions
            ;;
        3)
            log_info "Режим: Полный цикл"
            check_dependencies
            check_env_vars
            install_dependencies
            init_database
            test_connections
            prepare_render_deploy
            git_operations
            show_render_instructions
            health_check
            ;;
        *)
            log_error "Неверный выбор"
            exit 1
            ;;
    esac
    
    echo ""
    log_success "Деплой завершен успешно! 🚀"
    echo ""
}

# Обработка сигналов
trap 'echo ""; log_error "Деплой прерван пользователем"; exit 1' INT TERM

# Запуск основной функции
main "$@"
