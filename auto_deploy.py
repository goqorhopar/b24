#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import logging
import requests
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_deploy.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """Выполнить команду и вернуть результат"""
    try:
        logger.info(f"Executing: {command}")
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            logger.info(f"Command successful: {command}")
            return True, result.stdout
        else:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        logger.error(f"Exception running command {command}: {e}")
        return False, str(e)

def deploy_to_server():
    """Деплой на сервер"""
    try:
        logger.info("Starting deployment to server...")
        
        # Проверяем наличие необходимых файлов
        required_files = ['router.py', 'prompts.json', 'tools.json', 'mcp.json']
        for file in required_files:
            if not os.path.exists(file):
                logger.error(f"Required file missing: {file}")
                return False
        
        # Создаем архив для деплоя
        logger.info("Creating deployment archive...")
        success, output = run_command("tar -czf bot_deploy.tar.gz router.py prompts.json tools.json mcp.json mcp_test_request.json")
        if not success:
            logger.error("Failed to create deployment archive")
            return False
        
        # Копируем файлы на сервер (если настроен SSH)
        # Здесь можно добавить реальный деплой на сервер
        logger.info("Deployment archive created successfully")
        
        # Запускаем MCP сервер для тестирования
        logger.info("Testing MCP server...")
        success, output = run_command("python router.py --test")
        if not success:
            logger.error("MCP server test failed")
            return False
        
        logger.info("Deployment completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("Auto-deploy script started")
    
    # Создаем директорию для логов
    os.makedirs('logs', exist_ok=True)
    
    # Выполняем деплой
    success = deploy_to_server()
    
    if success:
        logger.info("Auto-deploy completed successfully")
        sys.exit(0)
    else:
        logger.error("Auto-deploy failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
