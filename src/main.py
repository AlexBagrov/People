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
        self.bot_token = os.getenv('TELEGRAM_TIGER_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        # Диагностика переменных окружения
        logger.info(f"TELEGRAM_TIGER_BOT_TOKEN exists: {bool(self.bot_token)}")
        logger.info(f"TELEGRAM_CHAT_ID exists: {bool(self.chat_id)}")
        
        if not self.bot_token or not self.chat_id:
            logger.error("TELEGRAM_TIGER_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment variables")
            logger.error("Please check GitHub Secrets configuration")
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
        
        # Диагностика переменных окружения
        logger.info(f"SUPABASE_URL exists: {bool(supabase_url)}")
        logger.info(f"SUPABASE_ANON_KEY exists: {bool(supabase_key)}")
        
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL or SUPABASE_ANON_KEY not found in environment variables")
            logger.error("Please check GitHub Secrets configuration")
            raise ValueError("Missing Supabase credentials")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        
        # Диагностика: попробуем получить информацию о доступных таблицах
        try:
            logger.info("Attempting to get database schema info...")
            # Простой запрос для проверки подключения
            test_response = self.supabase.from_('contact').select('count').limit(1).execute()
            logger.info(f"Database connection test successful")
        except Exception as e:
            logger.warning(f"Database schema check failed: {e}")
            logger.info("Continuing with main functionality...")
    
    def get_contact_data(self):
        """Получаем записи из таблицы contact с выбранными полями"""
        try:
            logger.info("Attempting to fetch name and message data from contact table...")
            # Выбираем только нужные поля
            response = self.supabase.from_('contact').select('name, message').execute()
            
            logger.info(f"Raw response: {response}")
            logger.info(f"Response data: {response.data}")
            logger.info(f"Response count: {len(response.data) if response.data else 0}")
            
            if response.data:
                logger.info(f"First record: {response.data[0]}")
                logger.info(f"Columns in first record: {list(response.data[0].keys())}")
            
            logger.info(f"Found {len(response.data)} records in contact table")
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch contact data: {e}")
            logger.error(f"Exception type: {type(e)}")
            return []
    
    def format_contact_table(self, contacts, header_text="📋 Сообщения от пользователей:", footer_text=""):
        """Форматируем данные контактов в таблицу с заголовками и дополнительным текстом"""
        if not contacts:
            return f"{header_text}\n\n📋 Таблица contact пуста"
        
        # Получаем заголовки из первой записи
        headers = list(contacts[0].keys())
        logger.info(f"Formatting table with {len(headers)} columns: {headers}")
        
        # Создаем HTML таблицу
        table_html = f"<b>{header_text}</b>\n\n"
        table_html += "<pre>\n"
        
        # Заголовки
        header_row = " | ".join(str(header) for header in headers)
        table_html += header_row + "\n"
        table_html += "-" * len(header_row) + "\n"
        
        # Данные
        for i, contact in enumerate(contacts):
            row = " | ".join(str(contact.get(header, '')) for header in headers)
            table_html += row + "\n"
            # Логируем первую запись для диагностики
            if i == 0:
                logger.info(f"First row data: {contact}")
        
        table_html += "</pre>"
        
        # Добавляем дополнительный текст в конце
        if footer_text:
            table_html += f"\n{footer_text}"
        
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
        
        logger.info(f"Contacts data received: {contacts}")
        logger.info(f"Contacts type: {type(contacts)}")
        logger.info(f"Contacts length: {len(contacts) if contacts else 0}")
        
        # Настраиваем дополнительные параметры
        current_time = datetime.now().strftime('%H:%M %d.%m.%Y')
        
        # Получаем настройки из переменных окружения или используем значения по умолчанию
        custom_header = os.getenv('CUSTOM_HEADER', f"📋 Сообщения от пользователей ({current_time}):")
        custom_footer = os.getenv('CUSTOM_FOOTER', f"✅ Всего сообщений: {len(contacts)} | Время отправки: {current_time}")
        
        header_text = custom_header
        footer_text = custom_footer
        
        if not contacts:
            logger.info("No data found in contact table")
            # Отправляем сообщение о том, что бот работает
            bot.send_message(f"✅ Бот работает! Время: {current_time}\n📋 Таблица contact пуста")
            return
        
        # Форматируем данные в таблицу с дополнительным текстом
        formatted_table = db.format_contact_table(contacts, header_text, footer_text)
        
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
