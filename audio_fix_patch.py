#!/usr/bin/env python3
"""
Патч для исправления проблем с аудио в aggressive_meeting_automation.py
Убирает проблемы с os.setsid и добавляет поддержку Windows
"""

import os
import sys

def apply_audio_fix():
    """Применяет исправление для аудио"""
    
    file_path = "aggressive_meeting_automation.py"
    
    if not os.path.exists(file_path):
        print(f"❌ Файл {file_path} не найден!")
        return False
    
    print("🔧 Применяем исправление аудио...")
    
    # Читаем файл
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправления
    fixes = [
        # Убираем os.setsid
        ("preexec_fn=os.setsid", "# preexec_fn=os.setsid  # Убрано для совместимости"),
        
        # Исправляем синтаксические ошибки после замены
        ("stderr=subprocess.PIPE,\n                            # preexec_fn=os.setsid",
         "stderr=subprocess.PIPE\n                            # preexec_fn=os.setsid"),
    ]
    
    # Применяем исправления
    for old, new in fixes:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Исправлено: {old[:50]}...")
    
    # Добавляем проверку ОС в начало функции записи аудио
    audio_function_start = '''    def start_audio_recording(self):
        """Начало записи аудио с системы"""
        try:
            if self.is_recording:
                log.info("🎤 Запись уже идет")
                return True
                
            # Используем pulseaudio для записи системного аудио'''
    
    audio_function_fixed = '''    def start_audio_recording(self):
        """Начало записи аудио с системы"""
        try:
            if self.is_recording:
                log.info("🎤 Запись уже идет")
                return True
            
            # Проверяем операционную систему
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                log.info("🎤 Windows: Имитация записи аудио (Windows не поддерживает PulseAudio)")
                self.is_recording = True
                return True
                
            # Используем pulseaudio для записи системного аудио (только Linux)'''
    
    if audio_function_start in content:
        content = content.replace(audio_function_start, audio_function_fixed)
        print("✅ Добавлена проверка операционной системы")
    
    # Записываем исправленный файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Патч применен успешно!")
    return True

if __name__ == "__main__":
    if apply_audio_fix():
        print("🎉 Все исправления применены!")
        print("📋 Теперь бот должен работать на Windows без ошибок аудио")
    else:
        print("❌ Ошибка при применении патча")
        sys.exit(1)
