# People - Telegram Bot с Supabase

Проект для отправки уведомлений из базы данных Supabase в Telegram.

## Структура проекта

```
People/
├── src/
│   └── main.py              # Основной код бота
├── .github/
│   └── workflows/
│       └── telegram-bot.yml # GitHub Actions workflow
├── requirements.txt         # Зависимости Python
├── README.md               # Документация
└── .gitignore             # Игнорируемые файлы
```

## Настройка

### 1. Создание Telegram бота

1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните токен бота

### 2. Получение Chat ID

1. Добавьте бота в нужный чат/канал
2. Отправьте сообщение в чат
3. Перейдите по ссылке: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Найдите `chat_id` в ответе

### 3. Настройка Supabase

1. Создайте проект на [supabase.com](https://supabase.com)
2. Создайте таблицу `messages`:

```sql
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP
);
```

3. Получите URL и API ключ из настроек проекта

### 4. Настройка GitHub Secrets

В настройках репозитория (Settings → Secrets and variables → Actions) добавьте:

- `SUPABASE_URL` - URL вашего Supabase проекта
- `SUPABASE_ANON_KEY` - Anon/Public ключ Supabase
- `TELEGRAM_BOT_TOKEN` - Токен вашего Telegram бота
- `TELEGRAM_CHAT_ID` - ID чата для отправки сообщений

## Использование

### Быстрый старт

1. **Создайте таблицу в Supabase:**
```sql
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP
);
```

2. **Добавьте тестовое сообщение:**
```sql
INSERT INTO messages (content, status) 
VALUES ('🎉 Первое сообщение из БД!', 'pending');
```

3. **Настройте GitHub Secrets** (если еще не настроили):
   - `SUPABASE_URL` - URL вашего Supabase проекта
   - `SUPABASE_ANON_KEY` - Anon/Public ключ Supabase
   - `TELEGRAM_BOT_TOKEN` - Токен вашего бота
   - `TELEGRAM_CHAT_ID` - ID канала

4. **Запустите GitHub Actions:**
   - Перейдите в Actions → Telegram Bot Notifications
   - Нажмите "Run workflow" → "Run workflow"

### Локальный запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте файл `.env` на основе `env.example`:
```bash
cp env.example .env
# Отредактируйте .env файл своими данными
```

3. Запустите тест:
```bash
python test_bot.py
```

### GitHub Actions

Бот автоматически запускается:
- По расписанию (8:00 и 18:00 UTC)
- При изменениях в папке `src/`
- Ручной запуск через GitHub Actions

## Добавление сообщений в базу данных

```sql
INSERT INTO messages (content, status) 
VALUES ('Ваше сообщение', 'pending');
```

## Логирование

Бот ведет подробные логи всех операций, включая:
- Подключение к базе данных
- Отправку сообщений
- Ошибки и их обработку

## Безопасность

- Все чувствительные данные хранятся в GitHub Secrets
- Используется анонимный ключ Supabase
- Логи не содержат чувствительной информации