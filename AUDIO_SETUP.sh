#!/bin/bash
# AUDIO_SETUP.sh - Скрипт для настройки аудиосистемы на VPS

echo "🔊 НАСТРОЙКА АУДИОСИСТЕМЫ НА VPS"
echo "================================="

# 1. Устанавливаем необходимые пакеты
echo "📦 Устанавливаю аудиопакеты..."
sudo apt-get update
sudo apt-get install -y pulseaudio pulseaudio-utils alsa-utils pavucontrol

# 2. Проверяем статус PulseAudio
echo "🔍 Проверяю статус PulseAudio..."
systemctl --user status pulseaudio || echo "PulseAudio не запущен"

# 3. Запускаем PulseAudio если не запущен
echo "🚀 Запускаю PulseAudio..."
pulseaudio --start || echo "Не удалось запустить PulseAudio"

# 4. Проверяем доступные устройства
echo "🔍 Проверяю доступные аудиоустройства..."
echo ""
echo "=== SINK-УСТРОЙСТВА (выход звука) ==="
pactl list short sinks
echo ""
echo "=== SINK-МОНИТОРЫ (для записи) ==="
pactl list short sinks | grep .monitor
echo ""
echo "=== ИСТОЧНИКИ ЗВУКА (микрофоны) ==="
pactl list short sources
echo ""

# 5. Создаем виртуальное аудиоустройство если нужно
echo "🎛️ Настраиваю виртуальные аудиоустройства..."
pactl load-module module-null-sink sink_name=virtual_speaker sink_properties=device.description="Virtual Speaker" || echo "Модуль уже загружен"
pactl load-module module-null-sink sink_name=virtual_microphone sink_properties=device.description="Virtual Microphone" || echo "Модуль уже загружен"

# 6. Проверяем модули PulseAudio
echo "🔍 Проверяю загруженные модули PulseAudio..."
pactl list short modules | grep null-sink

# 7. Тестируем запись
echo "🎤 Тестирую запись аудио..."
TEST_FILE="/tmp/audio_test_$(date +%s).wav"
echo "Тестовый файл: $TEST_FILE"

# Пробуем записать 3 секунды тестового звука
timeout 3s parecord --file-format=wav --channels=2 --rate=44100 "$TEST_FILE" 2>&1 || echo "Запись не удалась"

if [ -f "$TEST_FILE" ]; then
    echo "✅ Тестовая запись создана: $TEST_FILE"
    ls -la "$TEST_FILE"
    rm -f "$TEST_FILE"
else
    echo "❌ Тестовая запись не создана"
fi

# 8. Показываем информацию о системе
echo "💻 Информация о системе:"
echo "ОС: $(lsb_release -d | cut -f2)"
echo "Ядро: $(uname -r)"
echo "Архитектура: $(uname -m)"

# 9. Проверяем права пользователя
echo "👤 Проверяю права пользователя..."
groups
id

echo ""
echo "🎉 НАСТРОЙКА АУДИОСИСТЕМЫ ЗАВЕРШЕНА!"
echo "📋 Для проверки аудиоустройств: pactl list short sinks"
echo "📋 Для тестирования записи: parecord test.wav"
echo "📋 Для остановки записи: Ctrl+C"
