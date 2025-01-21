import os
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Чтение токена из переменной окружения
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("⚠️ Токен не найден! Убедитесь, что переменная окружения 'TOKEN' настроена.")

KEY_WETHER = os.getenv("KEY_WETHER")

if not KEY_WETHER:
    raise ValueError("⚠️ Ключ с погодой не найден! Убедитесь, что переменная окружения 'KEY_WETHER' настроена.")

DATABASE = os.getenv("DATABASE")

if not DATABASE:
    raise ValueError("⚠️ База данных не найдена! Убедитесь, что переменная окружения 'DATABASE' настроена.")