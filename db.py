import psycopg2
from psycopg2 import pool, OperationalError
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

connection_pool = None

def init_db_pool():
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 
            10, 
            dsn=Config.DATABASE_URL
        )
        if connection_pool:
            logger.info("Пул соединений успешно создан")
            return True
    except OperationalError as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
        connection_pool = None
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании пула: {e}")
        connection_pool = None
        return False


def get_db_connection():
    global connection_pool
    if connection_pool is None:
        logger.warning("Пул не инициализирован. Попытка создания...")
        if not init_db_pool():
            return None
    try:
        connection = connection_pool.getconn()
        logger.debug("Соединение получено из пула")
        return connection
    except OperationalError as e:
        logger.error(f"Ошибка получения соединения: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return None


def release_db_connection(connection):
    global connection_pool
    if connection and connection_pool:
        try:
            connection_pool.putconn(connection)
            logger.debug("Соединение возвращено в пул")
        except Exception as e:
            logger.error(f"Ошибка возврата соединения: {e}")


def close_all_connections():
    global connection_pool
    if connection_pool:
        try:
            connection_pool.closeall()
            logger.info("Все соединения закрыты")
        except Exception as e:
            logger.error(f"Ошибка закрытия соединений: {e}")
