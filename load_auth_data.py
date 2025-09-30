#!/usr/bin/env python3
"""
Модуль для загрузки сохраненных данных авторизации
Используется в основном боте для автоматического входа
"""

import os
import json
import time
from typing import Dict, List, Optional

class AuthDataLoader:
    """Класс для загрузки и применения сохраненных данных авторизации"""
    
    def __init__(self):
        self.cookies_path = "cookies.json"
        self.selenium_cookies_path = "selenium_cookies.json"
        self.storage_path = "storage.json"
        
    def load_playwright_cookies(self) -> Optional[List[Dict]]:
        """Загрузить cookies для Playwright"""
        try:
            if os.path.exists(self.cookies_path):
                with open(self.cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                print(f"✅ Загружены Playwright cookies: {len(cookies)} записей")
                return cookies
            else:
                print(f"⚠️ Файл {self.cookies_path} не найден")
                return None
        except Exception as e:
            print(f"❌ Ошибка загрузки Playwright cookies: {e}")
            return None
    
    def load_selenium_cookies(self) -> Optional[List[Dict]]:
        """Загрузить cookies для Selenium"""
        try:
            if os.path.exists(self.selenium_cookies_path):
                with open(self.selenium_cookies_path, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                print(f"✅ Загружены Selenium cookies: {len(cookies)} записей")
                return cookies
            else:
                print(f"⚠️ Файл {self.selenium_cookies_path} не найден")
                return None
        except Exception as e:
            print(f"❌ Ошибка загрузки Selenium cookies: {e}")
            return None
    
    def load_storage_data(self) -> Optional[Dict]:
        """Загрузить данные storage"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    storage = json.load(f)
                print(f"✅ Загружены storage данные")
                return storage
            else:
                print(f"⚠️ Файл {self.storage_path} не найден")
                return None
        except Exception as e:
            print(f"❌ Ошибка загрузки storage данных: {e}")
            return None
    
    def apply_selenium_cookies(self, driver) -> bool:
        """Применить cookies к Selenium драйверу"""
        try:
            cookies = self.load_selenium_cookies()
            if not cookies:
                return False
            
            # Сначала переходим на домен, чтобы установить cookies
            driver.get("https://google.com")
            time.sleep(1)
            
            applied_count = 0
            for cookie in cookies:
                try:
                    # Удаляем поля, которые могут вызвать ошибки
                    cookie_copy = cookie.copy()
                    cookie_copy.pop('sameSite', None)
                    cookie_copy.pop('httpOnly', None)
                    cookie_copy.pop('secure', None)
                    
                    driver.add_cookie(cookie_copy)
                    applied_count += 1
                except Exception as e:
                    # Игнорируем ошибки для отдельных cookies
                    continue
            
            print(f"✅ Применено {applied_count} cookies к Selenium драйверу")
            return applied_count > 0
            
        except Exception as e:
            print(f"❌ Ошибка применения cookies: {e}")
            return False
    
    def apply_storage_data(self, driver) -> bool:
        """Применить storage данные к драйверу"""
        try:
            storage_data = self.load_storage_data()
            if not storage_data:
                return False
            
            # Применяем localStorage
            if 'localStorage' in storage_data:
                for key, value in storage_data['localStorage'].items():
                    try:
                        driver.execute_script(f"window.localStorage.setItem('{key}', '{value}');")
                    except:
                        continue
            
            # Применяем sessionStorage
            if 'sessionStorage' in storage_data:
                for key, value in storage_data['sessionStorage'].items():
                    try:
                        driver.execute_script(f"window.sessionStorage.setItem('{key}', '{value}');")
                    except:
                        continue
            
            print("✅ Применены storage данные")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка применения storage данных: {e}")
            return False
    
    def check_auth_files_exist(self) -> Dict[str, bool]:
        """Проверить наличие файлов авторизации"""
        return {
            'playwright_cookies': os.path.exists(self.cookies_path),
            'selenium_cookies': os.path.exists(self.selenium_cookies_path),
            'storage_data': os.path.exists(self.storage_path)
        }
    
    def get_auth_status(self) -> str:
        """Получить статус авторизации"""
        files_status = self.check_auth_files_exist()
        
        if all(files_status.values()):
            return "✅ Полная авторизация доступна"
        elif files_status['selenium_cookies']:
            return "⚠️ Частичная авторизация (только cookies)"
        else:
            return "❌ Авторизация не настроена"
    
    def setup_authenticated_driver(self, driver) -> bool:
        """Настроить драйвер с авторизацией"""
        try:
            # Применяем cookies
            cookies_applied = self.apply_selenium_cookies(driver)
            
            # Применяем storage данные
            storage_applied = self.apply_storage_data(driver)
            
            if cookies_applied or storage_applied:
                print("✅ Драйвер настроен с авторизацией")
                return True
            else:
                print("⚠️ Не удалось применить данные авторизации")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка настройки авторизованного драйвера: {e}")
            return False

# Глобальный экземпляр для использования в других модулях
auth_loader = AuthDataLoader()

def get_auth_loader() -> AuthDataLoader:
    """Получить экземпляр загрузчика авторизации"""
    return auth_loader
