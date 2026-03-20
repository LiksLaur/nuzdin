from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from config import Config
from db import init_db_pool, close_all_connections
from models import (
    get_user_by_email, create_user, get_user_by_id, get_all_products,
    get_product_by_id, add_to_cart, get_cart_items, update_cart_item,
    remove_from_cart, place_order, get_user_orders,
    get_all_orders, get_order_details, update_order_status,
    create_product, update_product, delete_product
)
from werkzeug.security import check_password_hash
import logging
from functools import wraps

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    # Загрузка конфигурации
    app.config.from_object(config_class)
    # Инициализация пула соединений с БД
    with app.app_context():
        if not init_db_pool():
            logger.warning("Не удалось соединиться с БД.")
    # Регистрация маршрутов
    register_routes(app)
    # Регистрация обработчиков ошибок
    register_error_handlers(app)
    
    return app

# защита для незарегестрированных
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# защита для админа
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите.', 'warning')
            return redirect(url_for('login', next=request.url))
        if not session.get('is_admin', False):
            flash('Доступ запрещен. Требуются права администратора.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# сумма корзины
def get_cart_total(user_id):
    items = get_cart_items(user_id)
    return round(
        sum(item['quantity'] * item['price_at_time'] for item in items),
        2
    )

# маршруты
def register_routes(app):
    @app.route('/')
    def index():
        # главная стр
        return redirect(url_for('catalog'))
    @app.route('/catalog')
    def catalog():
        # каталог
        # Получаем параметры пагинации
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        # Ограничиваем per_page
        if per_page > 100:
            per_page = 100
        offset = (page - 1) * per_page
        # Получаем товары
        products = get_all_products(limit=per_page, offset=offset)
        # Проверяем, есть ли еще товары для следующей страницы
        has_next = len(products) == per_page
        return render_template(
            'catalog.html',
            products=products,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=page > 1
        )
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # рег пользователя
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            # Валидация
            if not email or not password:
                flash('Email и пароль обязательны.', 'danger')
                return render_template('register.html')
            if len(password) < 6:
                flash('Пароль должен быть не менее 6 символов.', 'danger')
                return render_template('register.html')
            if password != confirm_password:
                flash('Пароли не совпадают.', 'danger')
                return render_template('register.html')
            # Проверка униальности email
            existing_user = get_user_by_email(email)
            if existing_user:
                flash('Пользователь с таким email уже существует.', 'danger')
                return render_template('register.html')
            # Создание пользователя
            from werkzeug.security import generate_password_hash
            password_hash = generate_password_hash(password)
            user_id = create_user(email, password_hash, is_admin=False)
            # автовход
            if user_id:
                session['user_id'] = user_id
                session['email'] = email
                session['is_admin'] = False
                flash('Регистрация успешна!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Ошибка при регистрации. Попробуйте позже.', 'danger')
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # вход
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            if not email or not password:
                flash('Email и пароль обязательны.', 'danger')
                return render_template('login.html')
            user = get_user_by_email(email)
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['email'] = user['email']
                session['is_admin'] = user['is_admin']
                flash('С возвращением!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('index'))
            else:
                flash('Неверный email или пароль.', 'danger')
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        # выход
        session.clear()
        flash('Вы вышли из системы.', 'info')
        return redirect(url_for('index'))
    
    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        from models import get_product_by_id
        product = get_product_by_id(product_id)
        if not product:
            abort(404)
        return render_template('product_detail.html', product=product)
    
    @app.route('/add-to-cart/<int:product_id>', methods=['POST'])
    @login_required
    def add_to_cart_route(product_id):
        # добавление в корзину
        quantity = request.form.get('quantity', 1, type=int)
        if quantity <= 0:
            flash('Количество должно быть больше 0.', 'danger')
            return redirect(request.referrer or url_for('catalog'))
        product = get_product_by_id(product_id)
        if not product:
            flash('Товар не найден.', 'warning')
            return redirect(request.referrer or url_for('catalog'))
        if product.get('stock', 0) is not None and quantity > product['stock']:
            flash(f'Недостаточно товара на складе. Доступно: {product["stock"]}', 'warning')
            return redirect(request.referrer or url_for('catalog'))
        try:
            result = add_to_cart(session['user_id'], product_id, quantity)
            if result:
                flash(f'Товар добавлен в корзину (количество: {result})', 'success')
            else:
                flash('Ошибка при добавлении товара в корзину.', 'danger')
        except Exception as e:
            flash(str(e), 'danger')
        
        return redirect(request.referrer or url_for('catalog'))
    
    @app.route('/cart')
    @login_required
    def cart():
        # корзина
        items = get_cart_items(session['user_id'])
        total = get_cart_total(session['user_id'])
        return render_template('cart.html', items=items, total=total)
    
    @app.route('/update-cart-item/<int:item_id>', methods=['POST'])
    @login_required
    def update_cart_item_route(item_id):
        # обновление кол-ва
        quantity = request.form.get('quantity', 0, type=int)
        success = update_cart_item(item_id, quantity)
        if success:
            if quantity <= 0:
                flash('Товар удален из корзины.', 'success')
            else:
                flash('Количество товара обновлено.', 'success')
        else:
            flash('Ошибка при обновлении товара.', 'danger')
        
        return redirect(url_for('cart'))
    
    @app.route('/remove-from-cart/<int:item_id>', methods=['POST'])
    @login_required
    def remove_from_cart_route(item_id):
        # удаление товара
        success = remove_from_cart(item_id)
        if success:
            flash('Товар удален из корзины.', 'success')
        else:
            flash('Ошибка при удалении товара.', 'danger')
        return redirect(url_for('cart'))
    
    @app.route('/place-order', methods=['POST'])
    @login_required
    def place_order_route():
        # оформление заказа
        items = get_cart_items(session['user_id'])
        if not items:
            flash('Корзина пуста. Добавьте товары перед оформлением заказа.', 'warning')
            return redirect(url_for('cart'))
        changed = False
        for item in list(items):
            if item['stock'] <= 0:
                remove_from_cart(item['id'])
                changed = True
            elif item['quantity'] > item['stock']:
                update_cart_item(item['id'], item['stock'])
                changed = True

        if changed:
            flash('Некоторые товары были исключены/количество скорректировано из-за наличия на складе.', 'warning')
            items = get_cart_items(session['user_id'])
            if not items:
                flash('После проверки наличия корзина пуста.', 'warning')
                return redirect(url_for('cart'))
        try:
            order_id = place_order(session['user_id'])
            if order_id:
                flash(f'Заказ #{order_id} успешно оформлен!', 'success')
                return redirect(url_for('order_detail', order_id=order_id))
            else:
                flash('Ошибка при оформлении заказа.', 'danger')
        except Exception as e:
            flash(str(e), 'danger')
        return redirect(url_for('cart'))
    
    @app.route('/my-orders')
    @login_required
    def my_orders():
        # кабинет
        orders = get_user_orders(session['user_id'])
        for order in orders:
            items_list = order['items'] if 'items' in order else []
            order['total'] = round(sum(
                item['quantity'] * item['price_at_time'] 
                for item in items_list
            ), 2)
        
        return render_template('my_orders.html', orders=orders)

    @app.route('/order/<int:order_id>')
    @login_required
    def order_detail(order_id):
        order = get_order_details(order_id)
        if not order:
            abort(404)
        if not session.get('is_admin', False) and order.get('user_id') != session.get('user_id'):
            abort(403)

        total = round(sum(
            item['quantity'] * item['price_at_time']
            for item in order.get('items', [])
        ), 2)
        return render_template('order_detail.html', order=order, total=total)

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        # админка
        return render_template('admin_dashboard.html')

    @app.route('/admin/orders')
    @admin_required
    def admin_orders():
        # упрвлен заказами
        orders = get_all_orders(include_cart=False)
        for order in orders:
            details = get_order_details(order['id'])
            items_list = details['items'] if details and 'items' in details else []
            order['items'] = items_list
            order['total'] = round(sum(
                item['quantity'] * item['price_at_time']
                for item in items_list
            ), 2)
        return render_template('admin_orders.html', orders=orders)

    @app.route('/admin/order/<int:order_id>/update-status', methods=['POST'])
    @admin_required
    def admin_update_order_status(order_id):
        # обнавление статуса
        new_status = request.form.get('new_status')
        success = update_order_status(order_id, new_status)
        if success:
            flash('Статус заказа обновлен.', 'success')
        else:
            flash('Не удалось обновить статус заказа.', 'danger')
        return redirect(url_for('admin_orders'))

    @app.route('/admin/products', methods=['GET', 'POST'])
    @admin_required
    def admin_products():
        # упр товарами
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price')
            stock = request.form.get('stock')
            try:
                price = float(price) if price is not None else 0
            except (TypeError, ValueError):
                price = 0

            price = round(price, 2)
            try:
                stock = int(stock) if stock is not None else 0
            except (TypeError, ValueError):
                stock = 0
            success = create_product(name, description, price, stock)
            if success:
                flash('Товар добавлен.', 'success')
            else:
                flash('Не удалось добавить товар.', 'danger')
            return redirect(url_for('admin_products'))

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        if per_page > 100:
            per_page = 100
        offset = (page - 1) * per_page
        products = get_all_products(limit=per_page, offset=offset)
        has_next = len(products) == per_page
        return render_template(
            'admin_products.html',
            products=products,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=page > 1
        )

    @app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
    @admin_required
    def admin_edit_product(product_id):
        # редактирование товара
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price')
            stock = request.form.get('stock')
            try:
                price = float(price) if price is not None else 0
            except (TypeError, ValueError):
                price = 0
            price = round(price, 2)
            try:
                stock = int(stock) if stock is not None else 0
            except (TypeError, ValueError):
                stock = 0
            success = update_product(
                product_id,
                name=name,
                description=description,
                price=price,
                stock=stock
            )
            if success:
                flash('Товар обновлен.', 'success')
            else:
                flash('Не удалось обновить товар.', 'danger')
            return redirect(url_for('admin_products'))
        product = get_product_by_id(product_id)
        if not product:
            abort(404)
        return render_template('admin_product_edit.html', product=product)

    @app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
    @admin_required
    def admin_delete_product(product_id):
        # удаление товара через админа
        success = delete_product(product_id)
        if success:
            flash('Товар удален.', 'success')
        else:
            flash('Не удалось удалить товар.', 'danger')
        return redirect(url_for('admin_products'))
    
    # проверка
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'message': 'Приложение работает'}, 200

# ошибки
def register_error_handlers(app):
    # ошибка 400
    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"Страница не найдена: {error}")
        return render_template('404.html'), 404
    
    # ошибак 500
    @app.errorhandler(500)
    def internal_error(error):
        logger.exception("Внутренняя ошибка сервера")
        return render_template('500.html', message='Внутренняя ошибка сервера. Повторите попытку позже.'), 500
    
    # обработка искл
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Необработанное исключение: {error}")
        return render_template('500.html', message='Произошла непредвиденная ошибка. Повторите попытку позже.'), 500

# запуск
app = create_app()
import atexit
@atexit.register
def shutdown():
    close_all_connections()
    logger.info("Приложение остановлено")
if __name__ == '__main__':
    logger.info("Запуск Flask-приложения на http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
