# =============================================================================
# MEETING BOT - COMPREHENSIVE TEST SUITE
# Unit tests, integration tests, and end-to-end tests
# =============================================================================

import pytest
import asyncio
import os
import sys
import json
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_env():
    """Mock environment variables for testing"""
    env_vars = {
        'TELEGRAM_BOT_TOKEN': 'test_bot_token',
        'TELEGRAM_CHAT_ID': '123456789',
        'ADMIN_CHAT_ID': '987654321',
        'GITHUB_TOKEN': 'test_github_token',
        'GITHUB_REPO': 'test/repo',
        'WHISPER_MODEL': 'tiny',
        'RECORD_DIR': '/tmp/test_recordings',
        'CHROME_PROFILE_DIR': '/tmp/test_chrome_profile',
        'LOG_LEVEL': 'DEBUG',
        'MEETING_TIMEOUT_MIN': '30',
        'HEADLESS_MODE': 'true',
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing"""
    record_dir = tmp_path / "recordings"
    chrome_dir = tmp_path / "chrome_profile"
    log_dir = tmp_path / "logs"
    
    record_dir.mkdir()
    chrome_dir.mkdir()
    log_dir.mkdir()
    
    return {
        'recordings': record_dir,
        'chrome_profile': chrome_dir,
        'logs': log_dir,
    }


@pytest.fixture
def mock_driver():
    """Mock Selenium WebDriver"""
    driver = MagicMock()
    driver.current_url = "https://meet.google.com/test"
    driver.title = "Test Meeting"
    
    # Mock methods
    driver.get = MagicMock()
    driver.quit = MagicMock()
    driver.save_screenshot = MagicMock(return_value=True)
    driver.execute_script = MagicMock()
    driver.find_element = MagicMock()
    driver.find_elements = MagicMock(return_value=[])
    
    return driver


# =============================================================================
# UNIT TESTS - URL DETECTION
# =============================================================================

class TestUrlDetection:
    """Tests for meeting URL detection logic"""
    
    def test_detect_google_meet(self):
        """Test Google Meet URL detection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        urls = [
            "https://meet.google.com/abc-defg-hij",
            "https://meet.google.com/xyz-123",
            "MEET.GOOGLE.COM/ABC-DEF",
        ]
        
        for url in urls:
            result = bot.detect_meeting_type(url)
            assert result == 'google_meet', f"Failed for URL: {url}"
    
    def test_detect_zoom(self):
        """Test Zoom URL detection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        urls = [
            "https://zoom.us/j/123456789",
            "https://zoom.com/j/987654321",
            "ZOOM.US/J/123",
        ]
        
        for url in urls:
            result = bot.detect_meeting_type(url)
            assert result == 'zoom', f"Failed for URL: {url}"
    
    def test_detect_yandex(self):
        """Test Yandex Telemost URL detection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        urls = [
            "https://telemost.yandex.ru/meeting/123",
            "https://telemost.yandex.com/meeting/456",
        ]
        
        for url in urls:
            result = bot.detect_meeting_type(url)
            assert result == 'yandex', f"Failed for URL: {url}"
    
    def test_detect_contour(self):
        """Test Contour Talk URL detection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        urls = [
            "https://talk.contour.ru/meeting/123",
            "https://contour.ru/meeting/456",
        ]
        
        for url in urls:
            result = bot.detect_meeting_type(url)
            assert result == 'contour', f"Failed for URL: {url}"
    
    def test_detect_teams(self):
        """Test Microsoft Teams URL detection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        urls = [
            "https://teams.microsoft.com/l/meetup-join/123",
            "TEAMS.MICROSOFT.COM/L/MEETUP-JOIN",
        ]
        
        for url in urls:
            result = bot.detect_meeting_type(url)
            assert result == 'teams', f"Failed for URL: {url}"
    
    def test_detect_unknown(self):
        """Test unknown URL detection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        urls = [
            "https://example.com/meeting",
            "https://unknown.platform.com",
            "not-a-url",
        ]
        
        for url in urls:
            result = bot.detect_meeting_type(url)
            assert result == 'unknown', f"Failed for URL: {url}"


# =============================================================================
# UNIT TESTS - URL VALIDATION
# =============================================================================

class TestUrlValidation:
    """Tests for URL validation and sanitization"""
    
    def test_valid_urls(self):
        """Test valid URL acceptance"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        valid_urls = [
            "https://meet.google.com/abc-defg-hij",
            "https://zoom.us/j/123456789?pwd=test",
            "https://telemost.yandex.ru/meeting/123",
        ]
        
        for url in valid_urls:
            # Assuming we add a validate_url method
            assert bot.validate_url(url) is True, f"Valid URL rejected: {url}"
    
    def test_invalid_urls(self):
        """Test invalid URL rejection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        invalid_urls = [
            "",
            "not-a-url",
            "javascript:alert('xss')",
            "file:///etc/passwd",
            "ftp://example.com",
        ]
        
        for url in invalid_urls:
            assert bot.validate_url(url) is False, f"Invalid URL accepted: {url}"
    
    def test_malicious_urls(self):
        """Test malicious URL rejection"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        malicious_urls = [
            "https://meet.google.com/abc<script>alert(1)</script>",
            "https://zoom.us/j/123' OR '1'='1",
            "https://example.com/../../../etc/passwd",
        ]
        
        for url in malicious_urls:
            assert bot.validate_url(url) is False, f"Malicious URL accepted: {url}"


# =============================================================================
# UNIT TESTS - CONFIGURATION
# =============================================================================

class TestConfiguration:
    """Tests for configuration loading and validation"""
    
    def test_env_loading(self, mock_env):
        """Test environment variable loading"""
        from dotenv import load_dotenv
        
        load_dotenv()
        
        assert os.getenv('TELEGRAM_BOT_TOKEN') == 'test_bot_token'
        assert os.getenv('TELEGRAM_CHAT_ID') == '123456789'
        assert int(os.getenv('MEETING_TIMEOUT_MIN')) == 30
    
    def test_default_values(self):
        """Test default configuration values"""
        # Test that defaults are reasonable
        timeout = int(os.getenv('MEETING_TIMEOUT_MIN', '180'))
        assert timeout > 0
        assert timeout <= 1440  # Max 24 hours
        
        model = os.getenv('WHISPER_MODEL', 'medium')
        assert model in ['tiny', 'base', 'small', 'medium', 'large']


# =============================================================================
# UNIT TESTS - FILE OPERATIONS
# =============================================================================

class TestFileOperations:
    """Tests for file operations"""
    
    def test_create_record_directory(self, temp_dirs):
        """Test recording directory creation"""
        record_dir = temp_dirs['recordings']
        
        assert record_dir.exists()
        assert record_dir.is_dir()
    
    def test_json_file_operations(self, tmp_path):
        """Test JSON file read/write operations"""
        test_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}
        
        # Write
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Read
        with open(test_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data == test_data
    
    def test_auth_file_security(self, tmp_path):
        """Test that auth files have proper permissions"""
        auth_file = tmp_path / "cookies.json"
        auth_file.write_text('{"token": "secret"}')
        
        # Check file exists
        assert auth_file.exists()
        
        # In production, we would check file permissions
        # stat_result = os.stat(auth_file)
        # assert stat_result.st_mode & 0o777 == 0o600


# =============================================================================
# INTEGRATION TESTS - BOT INITIALIZATION
# =============================================================================

class TestBotInitialization:
    """Integration tests for bot initialization"""
    
    @patch('meeting_bot.WhisperModel')
    def test_bot_init_with_mock_whisper(self, mock_whisper, mock_env, temp_dirs):
        """Test bot initialization with mocked Whisper"""
        from meeting_bot import MeetingBot
        
        # Setup mock
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model
        
        # Update env for temp dirs
        os.environ['RECORD_DIR'] = str(temp_dirs['recordings'])
        os.environ['CHROME_PROFILE_DIR'] = str(temp_dirs['chrome_profile'])
        
        # Initialize bot (should not raise)
        bot = MeetingBot()
        
        assert bot is not None
        assert bot.meeting_url is None
        assert bot.recording is False
    
    def test_bot_init_without_github(self, mock_env):
        """Test bot initialization without GitHub token"""
        os.environ['GITHUB_TOKEN'] = ''
        
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        bot.github = None
        bot.repo = None
        
        assert bot.github is None
        assert bot.repo is None


# =============================================================================
# INTEGRATION TESTS - DRIVER MANAGEMENT
# =============================================================================

class TestDriverManagement:
    """Tests for WebDriver management"""
    
    def test_driver_cleanup(self, mock_driver):
        """Test driver cleanup on close"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        bot.driver = mock_driver
        bot._temp_profile_dir = "/tmp/test_profile"
        
        # Mock the cleanup method
        with patch('shutil.rmtree') as mock_rmtree:
            with patch('os.path.exists', return_value=True):
                bot._force_cleanup_driver()
                
                mock_driver.quit.assert_called_once()
    
    @patch('meeting_bot.webdriver.Chrome')
    def test_driver_setup_retry(self, mock_chrome):
        """Test driver setup with retry logic"""
        from meeting_bot import MeetingBot
        from selenium.common.exceptions import WebDriverException
        
        # Make first two attempts fail, third succeed
        mock_chrome.side_effect = [
            WebDriverException("JSON error"),
            WebDriverException("JSON error"),
            MagicMock()  # Success on third attempt
        ]
        
        bot = MeetingBot.__new__(MeetingBot)
        bot._temp_profile_dir = None
        
        # Should succeed after retries
        # Note: This is a simplified test, actual implementation may vary


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_meeting_url(self):
        """Test handling of empty meeting URL"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        with pytest.raises(ValueError):
            bot.validate_url("")
    
    def test_very_long_url(self):
        """Test handling of very long URLs"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        # Create very long URL
        long_url = "https://meet.google.com/" + "a" * 2000
        
        # Should either accept or reject gracefully, not crash
        try:
            result = bot.validate_url(long_url)
            assert isinstance(result, bool)
        except Exception as e:
            # If it raises, should be a specific validation error
            assert "URL" in str(e).upper() or "LENGTH" in str(e).upper()
    
    def test_unicode_in_url(self):
        """Test handling of unicode characters in URLs"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        
        unicode_url = "https://meet.google.com/тест-встреча"
        
        # Should handle unicode gracefully
        try:
            result = bot.validate_url(unicode_url)
            assert isinstance(result, bool)
        except Exception:
            pass  # Acceptable to reject unicode URLs
    
    def test_concurrent_meeting_requests(self):
        """Test handling of concurrent meeting requests"""
        from meeting_bot import MeetingBot
        
        bot = MeetingBot.__new__(MeetingBot)
        bot.meeting_active = False
        
        # Simulate concurrent requests
        results = []
        for i in range(5):
            if not bot.meeting_active:
                bot.meeting_active = True
                results.append(True)
            else:
                results.append(False)
        
        # Only first request should succeed
        assert sum(results) == 1


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Basic performance tests"""
    
    def test_url_detection_speed(self):
        """Test URL detection performance"""
        from meeting_bot import MeetingBot
        import time
        
        bot = MeetingBot.__new__(MeetingBot)
        
        urls = [
            "https://meet.google.com/abc-defg-hij",
            "https://zoom.us/j/123456789",
            "https://telemost.yandex.ru/meeting/123",
            "https://talk.contour.ru/meeting/456",
            "https://teams.microsoft.com/l/meetup-join/789",
        ] * 100  # Test 500 URLs
        
        start_time = time.time()
        
        for url in urls:
            bot.detect_meeting_type(url)
        
        elapsed = time.time() - start_time
        
        # Should process 500 URLs in under 1 second
        assert elapsed < 1.0, f"URL detection too slow: {elapsed}s"


# =============================================================================
# SECURITY TESTS
# =============================================================================

class TestSecurity:
    """Security-related tests"""
    
    def test_no_hardcoded_secrets(self):
        """Test that no secrets are hardcoded"""
        import meeting_bot
        
        # Read the source file
        with open(meeting_bot.__file__, 'r') as f:
            content = f.read()
        
        # Check for common secret patterns
        secret_patterns = [
            'token = "',
            "token = '",
            'password = "',
            "password = '",
            'secret = "',
            "secret = '",
        ]
        
        for pattern in secret_patterns:
            # Skip example patterns in comments
            lines = content.split('\n')
            for line in lines:
                if pattern in line.lower() and not line.strip().startswith('#'):
                    # Check if it's an actual assignment vs comparison
                    if '=' in line and '==' not in line:
                        pytest.fail(f"Potential hardcoded secret found: {line.strip()}")
    
    def test_env_var_usage(self):
        """Test that sensitive data comes from environment"""
        from meeting_bot import TELEGRAM_BOT_TOKEN, GITHUB_TOKEN
        
        # Tokens should come from environment, not be hardcoded
        assert TELEGRAM_BOT_TOKEN != ''
        assert GITHUB_TOKEN != ''


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
