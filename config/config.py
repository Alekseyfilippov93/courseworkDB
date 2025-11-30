from dotenv import load_dotenv
import os
from typing import Dict, Any

# Указываем, что .env находится в той же папке, что и этот файл
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def config(section: str = 'db') -> Dict[str, Any]:
    """Возвращает параметры для подключения к PostgreSQL или API,
    читая их из переменных окружения.
    """
    if section == 'db':
        # Преобразуем порт в int для psycopg2
        port_str = os.getenv('DB_PORT', '5432')
        db_port = int(port_str) if port_str.isdigit() else 5432

        return {
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': db_port
        }
    elif section == 'api':
        return {
            'base_url': os.getenv('API_URL_HH', 'https://api.hh.ru'),
            'headers': {
                'User-Agent': os.getenv('API_USER_AGENT', 'CourseworkDBManager (default)')
            }
        }
    return {}