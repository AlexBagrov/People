import os
import requests
from datetime import datetime
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            logger.error("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment variables")
            raise ValueError("Missing Telegram credentials")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        logger.info("Telegram bot initialized successfully")
    
    def send_message(self, text, parse_mode='HTML'):
        url = f"{self.base_url}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            logger.info(f"Message sent successfully: {text[:50]}...")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message: {e}")
            return False

class SupabaseManager:
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_ANON_KEY not found in environment variables")
            raise ValueError("Missing Supabase credentials")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
    
    def get_contact_data(self):
        """Получаем все записи из таблицы contact"""
        try:
            response = self.supabase.table('contact').select('*').execute()
            logger.info(f"Found {len(response.data)} records in contact table")
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch contact data: {e}")
            return []
    
    def format_contact_table(self, contacts):
        """Форматируем данные контактов в таблицу с заголовками"""
        if not contacts:
            return "📋 Таблица contact пуста"
        
        # Получаем заголовки из первой записи
        headers = list(contacts[0].keys())
        
        # Создаем HTML таблицу
        table_html = "<b>📋 Данные из таблицы contact:</b>\n\n"
        table_html += "<pre>\n"
        
        # Заголовки
        header_row = " | ".join(str(header) for header in headers)
        table_html += header_row + "\n"
        table_html += "-" * len(header_row) + "\n"
        
        # Данные
        for contact in contacts:
            row = " | ".join(str(contact.get(header, '')) for header in headers)
            table_html += row + "\n"
        
        table_html += "</pre>"
        
        return table_html

def main():
    logger.info("🚀 Starting Telegram bot job...")
    
    try:
        # Инициализация
        db = SupabaseManager()
        bot = TelegramBot()
        
        # Проверяем, есть ли тестовое сообщение из GitHub Actions
        test_message = os.getenv('TEST_MESSAGE')
        if test_message:
            logger.info("Sending manual test message")
            if bot.send_message(f"🧪 {test_message}"):
                logger.info("Test message sent successfully")
            return
        
        # Получаем данные из таблицы contact
        contacts = db.get_contact_data()
        
        if not contacts:
            logger.info("No data found in contact table")
            # Отправляем сообщение о том, что бот работает
            bot.send_message(f"✅ Бот работает! Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}\n📋 Таблица contact пуста")
            return
        
        # Форматируем данные в таблицу
        formatted_table = db.format_contact_table(contacts)
        
        # Отправляем таблицу
        if bot.send_message(formatted_table):
            logger.info(f"Contact table sent successfully with {len(contacts)} records")
        else:
            logger.error("Failed to send contact table")
        
        logger.info(f"✅ Job completed successfully. Sent {len(contacts)} contact records")
        
    except Exception as e:
        error_msg = f"❌ Error in Telegram bot: {str(e)}"
        logger.error(error_msg)
        
        # Пытаемся отправить уведомление об ошибке
        try:
            bot = TelegramBot()
            bot.send_message(error_msg)
        except:
            logger.error("Failed to send error notification to Telegram")
        
        raise

if __name__ == "__main__":
    main()
