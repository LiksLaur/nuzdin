from db import get_db_connection, release_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import logging
logger = logging.getLogger(__name__)

#ПОЛУЧЕНИЕ ПО ид
def get_user_by_id(user_id):
    connection = None
    cursor = None  
    try:
        connection = get_db_connection()
        if not connection:
            return None
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"Ошибка получения пользователя по ID {user_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# получение по емил
def get_user_by_email(email):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return None
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"Ошибка получения пользователя по email {email}: {e}")
        return None 
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# для создния нового пользователя
def create_user(email, password_hash, is_admin=False):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return None
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (email, password_hash, is_admin) VALUES (%s, %s, %s) RETURNING id",
            (email, password_hash, is_admin)
        )
        connection.commit()
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Ошибка создания пользователя {email}: {e}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# изменение пользователя
def update_user(user_id, **kwargs):
    if not kwargs:
        return False
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return False
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['email', 'password_hash', 'is_admin']:
                fields.append(f"{key} = %s")
                values.append(value)
        
        if not fields:
            return False
        values.append(user_id)
        query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s RETURNING id"
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
        if connection:
            connection.rollback()
        return False 
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)



# поучение всех продуктов для каталога
def get_all_products(limit=20, offset=0):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return []
            
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM products ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения товаров: {e}")
        return [] 
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# получение техники по ид
def get_product_by_id(product_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return None 
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    except Exception as e:
        logger.error(f"Ошибка получения товара по ID {product_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# создание продукта
def create_product(name, description, price, stock):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return None
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, description, price, stock)
        )
        connection.commit()
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Ошибка создания товара '{name}': {e}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# изменение продукта
def update_product(product_id, **kwargs):
    if not kwargs:
        return False
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return False
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'description', 'price', 'stock']:
                fields.append(f"{key} = %s")
                values.append(value)
        if not fields:
            return False
        
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(fields)} WHERE id = %s RETURNING id"
        cursor = connection.cursor()
        cursor.execute(query, values)
        connection.commit()
        row = cursor.fetchone()
        return row is not None
    except Exception as e:
        logger.error(f"Ошибка обновления товара {product_id}: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# удаление продукта
def delete_product(product_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return False  
        cursor = connection.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s RETURNING id", (product_id,))
        connection.commit()
        row = cursor.fetchone()
        return row is not None
        
    except Exception as e:
        logger.error(f"Ошибка удаления товара {product_id}: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)


# создание корзины
def get_or_create_cart(user_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return None
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM orders WHERE user_id = %s AND status = 'cart' ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        
        if row:
            return row[0]
        cursor.execute(
            "INSERT INTO orders (user_id, status) VALUES (%s, 'cart') RETURNING id",
            (user_id,)
        )
        connection.commit() 
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Ошибка получения/создания корзины для пользователя {user_id}: {e}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# добавление товаров в корзину
def add_to_cart(user_id, product_id, quantity=1):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return None
        # проверка
        cursor = connection.cursor()
        cursor.execute("SELECT stock, price FROM products WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        
        if not row:
            raise Exception("Товар не найден")
        stock, price = row
        if stock < quantity:
            raise Exception(f"Недостаточно товара на складе. Доступно: {stock}")
        
        # получение
        cart_id = get_or_create_cart(user_id)
        if not cart_id:
            raise Exception("Не удалось получить корзину")
        cursor.execute(
            "SELECT quantity FROM order_items WHERE order_id = %s AND product_id = %s",
            (cart_id, product_id)
        )
        existing_row = cursor.fetchone()
        if existing_row:
            new_quantity = existing_row[0] + quantity
            cursor.execute(
                "UPDATE order_items SET quantity = %s WHERE order_id = %s AND product_id = %s RETURNING quantity",
                (new_quantity, cart_id, product_id)
            )
        else:
            # Добавляем новый товар
            cursor.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price_at_time) VALUES (%s, %s, %s, %s) RETURNING quantity",
                (cart_id, product_id, quantity, price)
            )
        
        connection.commit()
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Ошибка добавления товара в корзину: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# полуение товаров из карзины пользователя
def get_cart_items(user_id):
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
            
        cursor = connection.cursor()
        cart_id = get_or_create_cart(user_id)
        if not cart_id:
            return []
        cursor.execute("""
            SELECT oi.id, oi.product_id, oi.quantity, oi.price_at_time,
                   p.name, p.description, p.stock
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (cart_id,))
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
        
    except Exception as e:
        logger.error(f"Ошибка получения товаров корзины: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# обновление кол-ва товара в орзине
def update_cart_item(order_item_id, quantity):
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return False
        cursor = connection.cursor()
        if quantity <= 0:
            cursor.execute("DELETE FROM order_items WHERE id = %s", (order_item_id,))
        else:
            cursor.execute(
                "UPDATE order_items SET quantity = %s WHERE id = %s RETURNING id",
                (quantity, order_item_id)
            )
        connection.commit()
        return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Ошибка обновления элемента корзины {order_item_id}: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# удаоление товара
def remove_from_cart(order_item_id):
    return update_cart_item(order_item_id, 0)

# оформление заказа
def place_order(user_id):
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return None    
        cursor = connection.cursor()
        cart_id = get_or_create_cart(user_id)
        if not cart_id:
            return None
        cursor.execute(
            "SELECT COUNT(*) FROM order_items WHERE order_id = %s",
            (cart_id,)
        )
        if cursor.fetchone()[0] == 0:
            raise Exception("Корзина пуста")
        

        cursor.execute("""
            UPDATE order_items oi
            SET price_at_time = p.price
            FROM products p
            WHERE oi.product_id = p.id AND oi.order_id = %s
        """, (cart_id,))
        cursor.execute(
            "UPDATE orders SET status = 'new' WHERE id = %s RETURNING id",
            (cart_id,)
        )
        connection.commit()
        row = cursor.fetchone()
        return row[0] if row else None
        
    except Exception as e:
        logger.error(f"Ошибка оформления заказа для пользователя {user_id}: {e}")
        if connection:
            connection.rollback()
        return None
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# получение заазов пользователя
def get_user_orders(user_id):
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
            
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, user_id, status, created_at
            FROM orders
            WHERE user_id = %s AND status != 'cart'
            ORDER BY created_at DESC
        """, (user_id,))
        
        orders = cursor.fetchall()
        order_columns = [desc[0] for desc in cursor.description]
        result = []
        for order_row in orders:
            order = dict(zip(order_columns, order_row))
            cursor.execute("""
                SELECT oi.id, oi.product_id, oi.quantity, oi.price_at_time, p.name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """, (order['id'],))
            
            items = cursor.fetchall()
            item_columns = [desc[0] for desc in cursor.description]
            order['items'] = [dict(zip(item_columns, item)) for item in items]
            result.append(order)
        return result 
    except Exception as e:
        logger.error(f"Ошибка получения заказов пользователя {user_id}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# получение инфы о заказах
def get_order_details(order_id):
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return None
            
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, user_id, status, created_at FROM orders WHERE id = %s",
            (order_id,)
        )
        
        row = cursor.fetchone()
        if not row:
            return None
        
        columns = [desc[0] for desc in cursor.description]
        order = dict(zip(columns, row))
        cursor.execute("""
            SELECT oi.id, oi.product_id, oi.quantity, oi.price_at_time, p.name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        """, (order_id,))
        items = cursor.fetchall()
        item_columns = [desc[0] for desc in cursor.description]
        order['items'] = [dict(zip(item_columns, item)) for item in items]
        return order
        
    except Exception as e:
        logger.error(f"Ошибка получения деталей заказа {order_id}: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# получение всех заказов
def get_all_orders(include_cart=False):
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        if not connection:
            return []
        cursor = connection.cursor()
        
        if include_cart:
            cursor.execute("""
                SELECT o.id, o.user_id, o.status, o.created_at, u.email
                FROM orders o
                JOIN users u ON o.user_id = u.id
                ORDER BY o.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT o.id, o.user_id, o.status, o.created_at, u.email
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE o.status != 'cart'
                ORDER BY o.created_at DESC
            """)
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения всех заказов: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)

# обновление статуса заказа
def update_order_status(order_id, new_status):
    valid_statuses = ['new', 'processing', 'completed', 'cancelled', 'cart']
    
    if new_status not in valid_statuses:
        logger.error(f"Недопустимый статус заказа: {new_status}")
        return False
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return False
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE orders SET status = %s WHERE id = %s RETURNING id",
            (new_status, order_id)
        )
        connection.commit()
        row = cursor.fetchone()
        return row is not None
        
    except Exception as e:
        logger.error(f"Ошибка обновления статуса заказа {order_id}: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            release_db_connection(connection)
