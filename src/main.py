import os
import requests
from datetime import datetime, timedelta
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
        """Получаем записи из таблицы contact по дате события"""
        try:
            # Вычисляем дату события для текущего года
            from datetime import datetime, timedelta
            
            # Получаем все записи с event_type = birthday
            response = self.supabase.from_('contact').select('name, message, event_date, event_type').eq('event_type', 'birthday').execute()
            
            logger.info(f"Found {len(response.data) if response.data else 0} birthday records")
            
            if not response.data:
                return []
            
            # Фильтруем записи, для которых сегодня нужно отправить напоминание
            current_date = datetime.now()
            target_records = []
            
            for record in response.data:
                event_date_str = record.get('event_date')
                if not event_date_str:
                    continue
                
                try:
                    # Парсим исходную дату события (например, "1989-09-05")
                    original_event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                    
                    # Создаем дату события для текущего года
                    current_year_event_date = datetime(
                        current_date.year, 
                        original_event_date.month, 
                        original_event_date.day
                    )
                    
                    # Вычисляем дату отправки (за 20 дней до события)
                    send_date = current_year_event_date - timedelta(days=20)
                    
                    # Проверяем, совпадает ли сегодняшняя дата с датой отправки
                    if current_date.date() == send_date.date():
                        target_records.append(record)
                        logger.info(f"Match found: {record.get('name')} - original: {event_date_str}, current year event: {current_year_event_date.strftime('%Y-%m-%d')}, send date: {send_date.strftime('%Y-%m-%d')}")
                
                except ValueError as e:
                    logger.warning(f"Invalid date format for record {record.get('name')}: {event_date_str}")
                    continue
            
            logger.info(f"Found {len(target_records)} records to send today")
            return target_records
        except Exception as e:
            logger.error(f"Failed to fetch contact data: {e}")
            logger.error(f"Exception type: {type(e)}")
            return []
    
    def format_contact_message(self, contacts, header_text="📋 Сообщения о днях рождения:", footer_text=""):
        """Форматируем данные в красивое сообщение для всех записей"""
        if not contacts:
            return f"{header_text}\n\n📋 На сегодня нет записей о днях рождения"
        
        logger.info(f"Formatting messages for {len(contacts)} records")
        
        # Создаем заголовок сообщения
        message_html = f"<b>{header_text}</b>\n\n"
        
        # Обрабатываем каждую запись
        for i, contact in enumerate(contacts):
            name = contact.get('name', 'Неизвестно')
            message = contact.get('message', 'Сообщение отсутствует')
            event_date = contact.get('event_date', 'Дата не указана')
            
            logger.info(f"Formatting message {i+1} for: {name}")
            logger.info(f"Message content: {message}")
            
            # Добавляем сообщение с эмодзи для дня рождения
            message_html += f"<b>{name}</b>: {message} 🎂\n"
            
            # Добавляем разделитель между записями (кроме последней)
            if i < len(contacts) - 1:
                message_html += "\n"
        
        # Добавляем дополнительный текст в конце
        if footer_text:
            message_html += f"\n\n{footer_text}"
        
        return message_html

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
        current_date = datetime.now().strftime('%d.%m.%Y')
        target_date = (datetime.now() + timedelta(days=20)).strftime('%d.%m.%Y')
        
        # Получаем настройки из переменных окружения или используем значения по умолчанию
        custom_header = os.getenv('CUSTOM_HEADER', f"📋 Напоминание о днях рождения ({target_date}):")
        custom_footer = os.getenv('CUSTOM_FOOTER', f"✅ Отправлено: {current_time}")
        
        header_text = custom_header
        footer_text = custom_footer
        
        if not contacts:
            logger.info("No birthday records found for target date")
            # Отправляем сообщение о том, что записей нет
            bot.send_message(f"✅ Бот работает! Время: {current_time}\n📋 На {target_date} нет записей о днях рождения")
            return
        
        # Форматируем данные в красивое сообщение
        formatted_message = db.format_contact_message(contacts, header_text, footer_text)
        
        # Отправляем сообщение
        if bot.send_message(formatted_message):
            logger.info(f"Birthday messages sent successfully for {len(contacts)} records")
        else:
            logger.error("Failed to send birthday messages")
        
        logger.info(f"✅ Job completed successfully. Sent {len(contacts)} birthday reminders")
        
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
