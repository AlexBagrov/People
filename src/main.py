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
    
    def ensure_table_exists(self):
        """Создаем таблицу если она не существует (только для первого запуска)"""
        try:
            # Проверяем существование таблицы
            response = self.supabase.table('messages').select('id').limit(1).execute()
            logger.info("Table 'messages' exists")
        except Exception as e:
            logger.warning(f"Table might not exist: {e}")
            logger.info("Please create the 'messages' table in Supabase dashboard")
    
    def get_pending_messages(self):
        """Получаем неотправленные сообщения"""
        try:
            response = self.supabase.table('messages').select('*').eq('status', 'pending').order('created_at').execute()
            logger.info(f"Found {len(response.data)} pending messages")
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch pending messages: {e}")
            return []
    
    def mark_as_sent(self, message_id):
        """Отмечаем сообщение как отправленное"""
        try:
            response = self.supabase.table('messages').update({
                'status': 'sent',
                'sent_at': datetime.now().isoformat()
            }).eq('id', message_id).execute()
            
            logger.info(f"Message {message_id} marked as sent")
            return True
        except Exception as e:
            logger.error(f"Failed to mark message {message_id} as sent: {e}")
            return False
    
    def add_test_messages(self):
        """Добавляем тестовые сообщения для демонстрации"""
        test_messages = [
            {
                'content': f'🔔 Тестовое уведомление: {datetime.now().strftime("%H:%M %d.%m.%Y")}',
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            },
            {
                'content': f'📊 Ежедневный отчет за {datetime.now().strftime("%d.%m.%Y")}',
                'status': 'pending',
                'created_at': datetime.now().isoformat()
            }
        ]
        
        try:
            response = self.supabase.table('messages').insert(test_messages).execute()
            logger.info(f"Added {len(test_messages)} test messages")
            return True
        except Exception as e:
            logger.error(f"Failed to add test messages: {e}")
            return False

def main():
    logger.info("🚀 Starting Telegram bot job...")
    
    try:
        # Инициализация
        db = SupabaseManager()
        bot = TelegramBot()
        
        # Проверяем существование таблицы
        db.ensure_table_exists()
        
        # Проверяем, есть ли тестовое сообщение из GitHub Actions
        test_message = os.getenv('TEST_MESSAGE')
        if test_message:
            logger.info("Sending manual test message")
            if bot.send_message(f"🧪 {test_message}"):
                logger.info("Test message sent successfully")
            return
        
        # Добавляем тестовые данные (уберите после первого тестирования)
        # db.add_test_messages()
        
        # Получаем сообщения для отправки
        pending_messages = db.get_pending_messages()
        
        if not pending_messages:
            logger.info("No pending messages to send")
            # Отправляем сообщение о том, что бот работает
            bot.send_message(f"✅ Бот работает! Время: {datetime.now().strftime('%H:%M %d.%m.%Y')}")
            return
        
        logger.info(f"Processing {len(pending_messages)} pending messages")
        
        # Отправляем сообщения
        sent_count = 0
        for message in pending_messages:
            message_id = message['id']
            content = message['content']
            
            if bot.send_message(content):
                if db.mark_as_sent(message_id):
                    sent_count += 1
                    logger.info(f"Message {message_id} processed successfully")
                else:
                    logger.error(f"Failed to mark message {message_id} as sent")
            else:
                logger.error(f"Failed to send message {message_id}")
        
        # Отправляем итоговый отчет
        if sent_count > 0:
            summary = f"📨 Отправлено сообщений: {sent_count} из {len(pending_messages)}"
            bot.send_message(summary)
        
        logger.info(f"✅ Job completed successfully. Sent: {sent_count}/{len(pending_messages)}")
        
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
