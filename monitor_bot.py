#!/usr/bin/env python3
"""
Мониторинг Meeting Bot - проверяет работу бота и перезапускает при необходимости
"""

import os
import sys
import time
import subprocess
import requests
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotMonitor:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_chat_id = os.getenv('ADMIN_CHAT_ID')
        self.check_interval = 300  # 5 минут
        self.max_restart_attempts = 3
        self.restart_attempts = 0
        
    def send_telegram_notification(self, message):
        """Отправить уведомление в Telegram"""
        if not self.bot_token or not self.admin_chat_id:
            logger.warning("Telegram не настроен для уведомлений")
            return
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.admin_chat_id,
                'text': f"🤖 Meeting Bot Monitor\n\n{message}",
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("Уведомление отправлено в Telegram")
            else:
                logger.error(f"Ошибка отправки в Telegram: {response.text}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def send_startup_notification(self):
        """Отправить уведомление о запуске"""
        try:
            import socket
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            
            message = f"🚀 **Meeting Bot запущен на сервере!**\n\n"
            message += f"🖥️ Сервер: {hostname}\n"
            message += f"🌐 IP: {ip}\n"
            message += f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"📊 Статус: Готов к работе 24/7"
            
            self.send_telegram_notification(message)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления о запуске: {e}")
    
    def check_bot_status(self):
        """Проверить статус бота"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', 'meeting-bot'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() == 'active'
        except Exception as e:
            logger.error(f"Ошибка проверки статуса: {e}")
            return False
    
    def restart_bot(self):
        """Перезапустить бота"""
        try:
            logger.info("Перезапуск Meeting Bot...")
            subprocess.run(['systemctl', 'restart', 'meeting-bot'], timeout=30)
            time.sleep(10)  # Ждем запуска
            
            if self.check_bot_status():
                logger.info("Бот успешно перезапущен")
                self.restart_attempts = 0
                self.send_telegram_notification("✅ Бот перезапущен и работает")
                return True
            else:
                logger.error("Не удалось перезапустить бота")
                self.restart_attempts += 1
                return False
                
        except Exception as e:
            logger.error(f"Ошибка перезапуска: {e}")
            self.restart_attempts += 1
            return False
    
    def get_bot_logs(self, lines=50):
        """Получить последние логи бота"""
        try:
            result = subprocess.run(
                ['journalctl', '-u', 'meeting-bot', '-n', str(lines), '--no-pager'],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Ошибка получения логов: {e}")
            return "Не удалось получить логи"
    
    def monitor(self):
        """Основной цикл мониторинга"""
        logger.info("Запуск мониторинга Meeting Bot...")
        self.send_startup_notification()
        
        last_check = datetime.now()
        
        while True:
            try:
                current_time = datetime.now()
                
                # Проверяем статус бота
                if not self.check_bot_status():
                    logger.warning("Бот не работает!")
                    
                    if self.restart_attempts < self.max_restart_attempts:
                        logger.info(f"Попытка перезапуска {self.restart_attempts + 1}/{self.max_restart_attempts}")
                        
                        if self.restart_bot():
                            continue
                        else:
                            logger.error("Перезапуск не удался")
                    else:
                        logger.error("Превышено максимальное количество попыток перезапуска")
                        self.send_telegram_notification(
                            f"❌ КРИТИЧЕСКАЯ ОШИБКА!\n\n"
                            f"Бот не работает после {self.max_restart_attempts} попыток перезапуска.\n"
                            f"Требуется ручное вмешательство!\n\n"
                            f"Последние логи:\n```\n{self.get_bot_logs(20)}\n```"
                        )
                        self.restart_attempts = 0  # Сбрасываем счетчик
                
                # Отправляем статус каждые 24 часа
                if (current_time - last_check).total_seconds() > 86400:  # 24 часа
                    logger.info("Отправка ежедневного статуса")
                    self.send_telegram_notification(
                        f"📊 Ежедневный статус\n\n"
                        f"✅ Бот работает стабильно\n"
                        f"⏰ Время: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"🔄 Перезапусков: {self.restart_attempts}"
                    )
                    last_check = current_time
                
                # Ждем следующую проверку
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Мониторинг остановлен пользователем")
                self.send_telegram_notification("⏹️ Мониторинг остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(60)  # Ждем минуту при ошибке

def main():
    """Главная функция"""
    monitor = BotMonitor()
    monitor.monitor()

if __name__ == "__main__":
    main()
