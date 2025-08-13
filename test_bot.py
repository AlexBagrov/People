#!/usr/bin/env python3
"""
Простой скрипт для тестирования Telegram бота
"""

import os
from dotenv import load_dotenv
from src.main import main

if __name__ == "__main__":
    # Загружаем переменные окружения
    load_dotenv()
    
    # Проверяем наличие необходимых переменных
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("Создайте файл .env на основе env.example")
        exit(1)
    
    print("🚀 Запуск тестирования бота...")
    main()
