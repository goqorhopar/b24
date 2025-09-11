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

    python3 - <<'PY'
from db import init_db
try:
    init_db()
    print('База данных инициализирована успешно')
except Exception as e:
    print(f'Ошибка инициализации БД: {e}')
    raise
PY

    log_success "База данных готова"
}

# Тестирование соединений
test_connections() {
    log_info "Тестирование соединений..."

    # Тест Gemini
    python3 - <<'PY'
from gemini_client import test_gemini_connection
ok = False
try:
    ok = test_gemini_connection()
    print('✅ Gemini API OK' if ok else '❌ Gemini API недоступен')
except Exception as e:
    print('❌ Ошибка при тесте Gemini:', e)
    raise
if not ok:
    exit 1
PY

    # Тест Bitrix (если настроен)
    if [[ -n "$BITRIX_WEBHOOK_URL" ]]; then
        python3 - <<'PY' || true
from bitrix import test_bitrix_connection
try:
    ok = test_bitrix_connection()
    print('✅ Bitrix24 API работает' if ok else '⚠️ Bitrix24 API недоступен (не критично)')
except Exception as e:
    print('⚠️ Bitrix check error:', e)
PY
    else
        log_warning "BITRIX_WEBHOOK_URL не настроен"
    fi

    log_success "Тесты соединений завершены"
}

# Запуск приложения локально
run_locally() {
    log_info "Запуск приложения локально..."

    source venv/bin/activate

    python3 main.py
}

# Подготовка к деплою на Render
prepare_render_deploy() {
    log_info "Подготовка к деплою на Render..."

    if [[ ! -f "render.yaml" ]]; then
        log_warning "render.yaml не найден"
    fi

    if [[ ! -f "Procfile" ]]; then
        log_warning "Procfile не найден, создаю..."
        echo "web: gunicorn main:app --bind 0.0.0.0:\$PORT --workers 2 --timeout 120" > Procfile
    fi

    if [[ ! -f "requirements.txt" ]]; then
        log_error "requirements.txt не найден"
        exit 1
    fi

    log_success "Подготовка к Render деплою завершена"
}

# Git операции
git_operations() {
    log_info "Git операции..."

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

    if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
        git push
        log_success "Изменения отправлены"
    else
        log_warning "Remote не настроен — пропускаем push"
    fi
}

# Основной блок
case "$1" in
    install)
        load_env
        check_dependencies
        check_env_vars
        install_dependencies
        init_database
        ;;
    test)
        load_env
        test_connections
        ;;
    run)
        load_env
        run_locally
        ;;
    prepare_render)
        load_env
        prepare_render_deploy
        ;;
    deploy)
        load_env
        git_operations
        ;;
    *)
        echo "Использование: $0 {install|test|run|prepare_render|deploy}"
        exit 1
        ;;
esac
