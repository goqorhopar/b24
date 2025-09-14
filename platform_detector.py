"""
Модуль для автоматического определения платформы онлайн-встреч
"""
import re
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, parse_qs
from datetime import datetime

log = logging.getLogger(__name__)

class MeetingPlatformDetector:
    """Класс для определения платформы онлайн-встреч"""
    
    def __init__(self):
        self.platform_patterns = {
            'zoom': {
                'name': 'Zoom',
                'url_patterns': [
                    r'zoom\.us/j/',
                    r'zoom\.us/s/',
                    r'zoom\.us/w/',
                    r'zoom\.us/my/',
                    r'zoom\.us/webinar/',
                    r'zoom\.us/rec/',
                    r'[a-z0-9-]*\.zoom\.us/j/',
                    r'[a-z0-9-]*\.zoom\.us/s/',
                    r'[a-z0-9-]*\.zoom\.us/w/',
                ],
                'id_patterns': [
                    r'(?:[a-z0-9-]*\.)?zoom\.us/(?:j/|s/|w/)([\w-]+)',
                    r'(?:[a-z0-9-]*\.)?zoom\.us/my/([\w-]+)',
                ],
                'meeting_id_length': [9, 10, 11],
                'required_params': [],
                'optional_params': ['pwd', 'zak', 'cn', 'mc', 'role']
            },
            'google_meet': {
                'name': 'Google Meet',
                'url_patterns': [
                    r'meet\.google\.com/',
                    r'hangouts\.google\.com/call/',
                ],
                'id_patterns': [
                    r'meet\.google\.com/([\w-]{3}-[\w-]{4}-[\w-]{3})',
                    r'hangouts\.google\.com/call/([\w-]+)',
                ],
                'meeting_id_length': [12],  # abc-defg-hij
                'required_params': [],
                'optional_params': ['authuser']
            },
            'teams': {
                'name': 'Microsoft Teams',
                'url_patterns': [
                    r'teams\.microsoft\.com/l/meetup-join/',
                    r'teams\.microsoft\.com/l/channel/',
                    r'teams\.live\.com/',
                    r'teams\.microsoft\.com/dl/launcher/',
                ],
                'id_patterns': [
                    r'teams\.microsoft\.com/l/meetup-join/[^/]+/([^/?]+)',
                    r'teams\.live\.com/([^/?]+)',
                ],
                'meeting_id_length': [12, 13, 17],
                'required_params': [],
                'optional_params': ['p', 'anon', 'allowInvite']
            },
            'kontur_talk': {
                'name': 'Kontur Talk',
                'url_patterns': [
                    r'talk\.kontur\.ru/',
                    r'kontur\.ru/talk/',
                    r'kontur\.ru/meeting/',
                    r'ktalk\.ru/',
                    r'[a-z0-9-]*\.ktalk\.ru/',
                ],
                'id_patterns': [
                    r'talk\.kontur\.ru/([^/?]+)',
                    r'kontur\.ru/talk/([^/?]+)',
                    r'kontur\.ru/meeting/([^/?]+)',
                    r'(?:[a-z0-9-]*\.)?ktalk\.ru/([^/?]+)',
                ],
                'meeting_id_length': [8, 9, 10, 11, 12],
                'required_params': [],
                'optional_params': ['password', 'pin']
            },
            'yandex_telemost': {
                'name': 'Яндекс Телемост',
                'url_patterns': [
                    r'telemost\.yandex\.ru/j/',
                    r'telemost\.yandex\.ru/',
                ],
                'id_patterns': [
                    r'telemost\.yandex\.ru/j/([^/?]+)',
                    r'telemost\.yandex\.ru/([^/?]+)',
                ],
                'meeting_id_length': [10, 11, 12, 13, 14],
                'required_params': [],
                'optional_params': ['password', 'pin']
            }
        }
        
        # Дополнительные паттерны для обнаружения в тексте
        self.text_patterns = {
            'zoom': [
                r'zoom\s+meeting\s+id[:\s]*(\d+)',
                r'zoom\s+meeting\s+password[:\s]*(\w+)',
                r'join\s+zoom\s+meeting',
                r'zoom\.us',
                r'zoom\s+link',
            ],
            'google_meet': [
                r'google\s+meet',
                r'meet\.google\.com',
                r'join\s+google\s+meet',
                r'google\s+hangout',
            ],
            'teams': [
                r'microsoft\s+teams',
                r'teams\.microsoft\.com',
                r'join\s+teams\s+meeting',
                r'teams\s+live',
            ],
            'kontur_talk': [
                r'kontur\s+talk',
                r'talk\.kontur\.ru',
                r'kontur\.ru/talk',
                r'kontur\s+meeting',
            ],
            'yandex_telemost': [
                r'яндекс\s+телемост',
                r'telemost\.yandex\.ru',
                r'телемост\s+яндекс',
                r'яндекс\s+встреча',
            ]
        }
    
    def detect_platform_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Определить платформу из URL"""
        try:
            log.info(f"Анализ URL для определения платформы: {url}")
            
            # Нормализация URL
            normalized_url = self._normalize_url(url)
            if not normalized_url:
                return None
            
            # Парсинг URL
            parsed_url = urlparse(normalized_url)
            hostname = parsed_url.hostname.lower()
            path = parsed_url.path.lower()
            
            # Поиск платформы по паттернам
            for platform_key, platform_info in self.platform_patterns.items():
                # Проверка паттернов URL
                for pattern in platform_info['url_patterns']:
                    if re.search(pattern, hostname + path):
                        log.info(f"Обнаружена платформа: {platform_info['name']}")
                        
                        # Извлечение ID встречи
                        meeting_id = self._extract_meeting_id(normalized_url, platform_key)
                        
                        # Извлечение параметров
                        params = self._extract_url_params(parsed_url, platform_key)
                        
                        # Валидация
                        validation_result = self._validate_platform_detection(
                            platform_key, meeting_id, params
                        )
                        
                        return {
                            'platform': platform_key,
                            'platform_name': platform_info['name'],
                            'url': normalized_url,
                            'meeting_id': meeting_id,
                            'params': params,
                            'validation': validation_result,
                            'confidence': self._calculate_confidence(platform_key, meeting_id, params),
                            'detected_at': datetime.now().isoformat()
                        }
            
            log.warning("Платформа не определена по URL")
            return None
            
        except Exception as e:
            log.error(f"Ошибка при определении платформы из URL: {e}")
            return None
    
    def detect_platform_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Определить платформу из текста"""
        try:
            log.info("Анализ текста для определения платформы")
            
            detected_platforms = []
            
            for platform_key, patterns in self.text_patterns.items():
                platform_info = self.platform_patterns.get(platform_key)
                if not platform_info:
                    continue
                
                matches = []
                for pattern in patterns:
                    found_matches = re.findall(pattern, text, re.IGNORECASE)
                    matches.extend(found_matches)
                
                if matches:
                    detected_platforms.append({
                        'platform': platform_key,
                        'platform_name': platform_info['name'],
                        'matches': matches,
                        'confidence': self._calculate_text_confidence(platform_key, matches),
                        'detected_at': datetime.now().isoformat()
                    })
            
            # Сортировка по уверенности
            detected_platforms.sort(key=lambda x: x['confidence'], reverse=True)
            
            log.info(f"Обнаружено платформ в тексте: {len(detected_platforms)}")
            return detected_platforms
            
        except Exception as e:
            log.error(f"Ошибка при определении платформы из текста: {e}")
            return []
    
    def detect_platform_from_email(self, email_content: str) -> Optional[Dict[str, Any]]:
        """Определить платформу из содержимого email"""
        try:
            log.info("Анализ email для определения платформы")
            
            # Поиск URL в email
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, email_content)
            
            for url in urls:
                platform_info = self.detect_platform_from_url(url)
                if platform_info:
                    log.info(f"Платформа определена из email URL: {platform_info['platform_name']}")
                    return platform_info
            
            # Если URL не найдены, анализируем текст
            text_platforms = self.detect_platform_from_text(email_content)
            if text_platforms:
                best_match = text_platforms[0]
                log.info(f"Платформа определена из текста email: {best_match['platform_name']}")
                return {
                    'platform': best_match['platform'],
                    'platform_name': best_match['platform_name'],
                    'url': None,
                    'meeting_id': None,
                    'params': {},
                    'validation': {'valid': True, 'message': 'Detected from text'},
                    'confidence': best_match['confidence'],
                    'detected_at': datetime.now().isoformat()
                }
            
            log.warning("Платформа не определена из email")
            return None
            
        except Exception as e:
            log.error(f"Ошибка при определении платформы из email: {e}")
            return None
    
    def detect_platform(self, url: str) -> Optional[Dict[str, Any]]:
        """Основной метод определения платформы из URL"""
        try:
            log.info(f"Определение платформы для URL: {url}")
            
            # Сначала пробуем определить из URL
            platform_info = self.detect_platform_from_url(url)
            if platform_info:
                log.info(f"Платформа определена из URL: {platform_info['platform_name']}")
                return platform_info
            
            # Если не удалось из URL, пробуем из текста
            text_platforms = self.detect_platform_from_text(url)
            if text_platforms:
                best_match = text_platforms[0]
                log.info(f"Платформа определена из текста: {best_match['platform_name']}")
                return {
                    'platform': best_match['platform'],
                    'platform_name': best_match['platform_name'],
                    'url': url,
                    'meeting_id': None,
                    'params': {},
                    'validation': {'valid': True, 'message': 'Detected from text'},
                    'confidence': best_match['confidence'],
                    'detected_at': datetime.now().isoformat()
                }
            
            log.warning("Платформа не определена")
            return None
            
        except Exception as e:
            log.error(f"Ошибка при определении платформы: {e}")
            return None
    
    def detect_platform(self, url: str) -> Optional[Dict[str, Any]]:
        """Основной метод определения платформы из URL"""
        try:
            log.info(f"Определение платформы для URL: {url}")
            
            # Сначала пробуем определить из URL
            platform_info = self.detect_platform_from_url(url)
            if platform_info:
                log.info(f"Платформа определена из URL: {platform_info['platform_name']}")
                return platform_info
            
            # Если не удалось из URL, пробуем из текста
            text_platforms = self.detect_platform_from_text(url)
            if text_platforms:
                best_match = text_platforms[0]
                log.info(f"Платформа определена из текста: {best_match['platform_name']}")
                return {
                    'platform': best_match['platform'],
                    'platform_name': best_match['platform_name'],
                    'url': url,
                    'meeting_id': None,
                    'params': {},
                    'validation': {'valid': True, 'message': 'Detected from text'},
                    'confidence': best_match['confidence'],
                    'detected_at': datetime.now().isoformat()
                }
            
            log.warning("Платформа не определена")
            return None
            
        except Exception as e:
            log.error(f"Ошибка при определении платформы: {e}")
            return None
    
    def get_platform_info(self, platform_key: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о платформе"""
        return self.platform_patterns.get(platform_key)
    
    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        """Получить список поддерживаемых платформ"""
        platforms = []
        for key, info in self.platform_patterns.items():
            platforms.append({
                'key': key,
                'name': info['name'],
                'url_patterns': info['url_patterns'],
                'meeting_id_length': info['meeting_id_length']
            })
        return platforms
    
    def validate_meeting_url(self, url: str, platform_key: str) -> Dict[str, Any]:
        """Валидировать URL встречи для конкретной платформы"""
        try:
            platform_info = self.platform_patterns.get(platform_key)
            if not platform_info:
                return {'valid': False, 'message': f'Unsupported platform: {platform_key}'}
            
            # Нормализация URL
            normalized_url = self._normalize_url(url)
            if not normalized_url:
                return {'valid': False, 'message': 'Invalid URL format'}
            
            # Проверка паттернов
            parsed_url = urlparse(normalized_url)
            hostname = parsed_url.hostname.lower()
            path = parsed_url.path.lower()
            
            pattern_matched = False
            for pattern in platform_info['url_patterns']:
                if re.search(pattern, hostname + path):
                    pattern_matched = True
                    break
            
            if not pattern_matched:
                return {'valid': False, 'message': 'URL does not match platform patterns'}
            
            # Извлечение и валидация ID
            meeting_id = self._extract_meeting_id(normalized_url, platform_key)
            if not meeting_id:
                return {'valid': False, 'message': 'Meeting ID not found'}
            
            # Проверка длины ID
            id_length = len(meeting_id.replace('-', ''))
            if id_length not in platform_info['meeting_id_length']:
                return {'valid': False, 'message': f'Invalid meeting ID length: {id_length}'}
            
            # Проверка обязательных параметров
            params = self._extract_url_params(parsed_url, platform_key)
            for required_param in platform_info['required_params']:
                if required_param not in params:
                    return {'valid': False, 'message': f'Missing required parameter: {required_param}'}
            
            return {
                'valid': True,
                'message': 'URL is valid',
                'meeting_id': meeting_id,
                'params': params
            }
            
        except Exception as e:
            log.error(f"Ошибка при валидации URL: {e}")
            return {'valid': False, 'message': f'Validation error: {str(e)}'}
    
    def _normalize_url(self, url: str) -> Optional[str]:
        """Нормализовать URL"""
        try:
            # Удаление лишних пробелов
            url = url.strip()
            
            # Добавление протокола, если отсутствует
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Базовая валидация
            if not re.match(r'^https?://', url):
                return None
            
            return url
            
        except Exception as e:
            log.error(f"Ошибка при нормализации URL: {e}")
            return None
    
    def _extract_meeting_id(self, url: str, platform_key: str) -> Optional[str]:
        """Извлечь ID встречи из URL"""
        try:
            platform_info = self.platform_patterns.get(platform_key)
            if not platform_info:
                return None
            
            for pattern in platform_info['id_patterns']:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            log.error(f"Ошибка при извлечении ID встречи: {e}")
            return None
    
    def _extract_url_params(self, parsed_url, platform_key: str) -> Dict[str, str]:
        """Извлечь параметры URL"""
        try:
            platform_info = self.platform_patterns.get(platform_key)
            if not platform_info:
                return {}
            
            params = {}
            query_params = parse_qs(parsed_url.query)
            
            # Извлечение всех параметров
            for key, values in query_params.items():
                if values:
                    params[key] = values[0]
            
            # Фильтрация только релевантных параметров
            relevant_params = platform_info['required_params'] + platform_info['optional_params']
            filtered_params = {k: v for k, v in params.items() if k in relevant_params}
            
            return filtered_params
            
        except Exception as e:
            log.error(f"Ошибка при извлечении параметров URL: {e}")
            return {}
    
    def _validate_platform_detection(self, platform_key: str, meeting_id: Optional[str], 
                                   params: Dict[str, str]) -> Dict[str, Any]:
        """Валидировать определение платформы"""
        try:
            platform_info = self.platform_patterns.get(platform_key)
            if not platform_info:
                return {'valid': False, 'message': 'Unknown platform'}
            
            # Проверка ID
            if not meeting_id:
                return {'valid': False, 'message': 'Meeting ID not found'}
            
            # Проверка длины ID
            id_length = len(meeting_id.replace('-', ''))
            if id_length not in platform_info['meeting_id_length']:
                return {'valid': False, 'message': f'Invalid meeting ID length: {id_length}'}
            
            # Проверка обязательных параметров
            for required_param in platform_info['required_params']:
                if required_param not in params:
                    return {'valid': False, 'message': f'Missing required parameter: {required_param}'}
            
            return {'valid': True, 'message': 'Platform detection is valid'}
            
        except Exception as e:
            log.error(f"Ошибка при валидации определения платформы: {e}")
            return {'valid': False, 'message': f'Validation error: {str(e)}'}
    
    def _calculate_confidence(self, platform_key: str, meeting_id: Optional[str], 
                            params: Dict[str, str]) -> float:
        """Рассчитать уверенность в определении платформы"""
        try:
            confidence = 0.0
            
            # Базовый балл за определение платформы
            confidence += 50.0
            
            # Балл за наличие ID
            if meeting_id:
                confidence += 30.0
                
                # Дополнительный балл за правильную длину ID
                platform_info = self.platform_patterns.get(platform_key)
                if platform_info:
                    id_length = len(meeting_id.replace('-', ''))
                    if id_length in platform_info['meeting_id_length']:
                        confidence += 10.0
            
            # Балл за наличие параметров
            if params:
                confidence += min(len(params) * 5.0, 10.0)
            
            return min(confidence, 100.0)
            
        except Exception as e:
            log.error(f"Ошибка при расчете уверенности: {e}")
            return 0.0
    
    def _calculate_text_confidence(self, platform_key: str, matches: List[str]) -> float:
        """Рассчитать уверенность в определении платформы из текста"""
        try:
            if not matches:
                return 0.0
            
            confidence = 30.0  # Базовый балл за совпадения
            
            # Дополнительный балл за количество совпадений
            confidence += min(len(matches) * 10.0, 40.0)
            
            # Дополнительный балл за качество совпадений
            for match in matches:
                if any(keyword in match.lower() for keyword in ['meeting', 'join', 'link', 'id']):
                    confidence += 5.0
            
            return min(confidence, 100.0)
            
        except Exception as e:
            log.error(f"Ошибка при расчете уверенности из текста: {e}")
            return 0.0

class MeetingUrlParser:
    """Класс для парсинга и обработки URL встреч"""
    
    def __init__(self):
        self.detector = MeetingPlatformDetector()
    
    def parse_meeting_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Полный парсинг URL встречи"""
        try:
            log.info(f"Парсинг URL встречи: {url}")
            
            # Определение платформы
            platform_info = self.detector.detect_platform_from_url(url)
            if not platform_info:
                return None
            
            # Дополнительный парсинг
            parsed_url = urlparse(url)
            
            # Формирование полного результата
            result = {
                'original_url': url,
                'normalized_url': self.detector._normalize_url(url),
                'platform_info': platform_info,
                'url_components': {
                    'scheme': parsed_url.scheme,
                    'hostname': parsed_url.hostname,
                    'port': parsed_url.port,
                    'path': parsed_url.path,
                    'query': parsed_url.query,
                    'fragment': parsed_url.fragment
                },
                'is_valid': platform_info['validation']['valid'],
                'can_join': self._can_join_meeting(platform_info),
                'join_instructions': self._get_join_instructions(platform_info),
                'parsed_at': datetime.now().isoformat()
            }
            
            log.info(f"URL успешно распарсен: {platform_info['platform_name']}")
            return result
            
        except Exception as e:
            log.error(f"Ошибка при парсинге URL: {e}")
            return None
    
    def _can_join_meeting(self, platform_info: Dict[str, Any]) -> bool:
        """Проверить возможность присоединения к встрече"""
        return platform_info['validation']['valid']
    
    def _get_join_instructions(self, platform_info: Dict[str, Any]) -> List[str]:
        """Получить инструкции по присоединению"""
        platform = platform_info['platform']
        instructions = []
        
        if platform == 'zoom':
            instructions.extend([
                "Откройте URL в браузере",
                "Введите пароль, если требуется",
                "Дождитесь подключения к встрече"
            ])
        elif platform == 'google_meet':
            instructions.extend([
                "Откройте URL в браузере",
                "Войдите в аккаунт Google, если требуется",
                "Разрешите доступ к камере и микрофону"
            ])
        elif platform == 'teams':
            instructions.extend([
                "Откройте URL в браузере",
                "Войдите в аккаунт Microsoft, если требуется",
                "Выберите вариант присоединения (с приложением или в браузере)"
            ])
        elif platform == 'kontur_talk':
            instructions.extend([
                "Откройте URL в браузере",
                "Введите PIN-код, если требуется",
                "Дождитесь подключения к встрече"
            ])
        
        return instructions

# Функции для удобного использования
def detect_meeting_platform(url: str) -> Optional[Dict[str, Any]]:
    """Определить платформу встречи из URL"""
    detector = MeetingPlatformDetector()
    return detector.detect_platform_from_url(url)

def parse_meeting_url(url: str) -> Optional[Dict[str, Any]]:
    """Распарсить URL встречи"""
    parser = MeetingUrlParser()
    return parser.parse_meeting_url(url)

def get_supported_platforms() -> List[Dict[str, Any]]:
    """Получить список поддерживаемых платформ"""
    detector = MeetingPlatformDetector()
    return detector.get_supported_platforms()
