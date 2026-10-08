from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, abort
from models import db, User, Server, server_access
from ssh_utils import *
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO
from flask_caching import Cache
from flask_compress import Compress
import json
import requests
from sqlalchemy import text
import sys
import io
import logging
from logging.handlers import RotatingFileHandler

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# -----------------------------------------------
# Настройка логгера
# -----------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler для файла с ротацией
file_handler = RotatingFileHandler('logs/lavaferret.log', maxBytes=10*1024*1024, backupCount=5)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Handler для консоли
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# -----------------------------------------------
# Список версий для разных типов ядер
# -----------------------------------------------
versions = {
    'vanilla': ['26.2', '26.1.2', '26.1.1', '26.1', '1.21.11', '1.21.10', '1.21.9', '1.21.8', '1.21.7', '1.21.6',
                '1.21.5', '1.21.4', '1.21.3', '1.21.2', '1.21.1', '1.21', '1.20.6', '1.20.5', '1.20.4', '1.20.3',
                '1.20.2', '1.20.1', '1.20', '1.19.4', '1.19.3', '1.19.2', '1.19.1', '1.19', '1.18.2', '1.18.1', '1.18',
                '1.17.1', '1.17', '1.16.5', '1.16.4', '1.16.3', '1.16.2', '1.16.1', '1.16', '1.15.2', '1.15.1', '1.15',
                '1.14.4', '1.14.3', '1.14.2', '1.14.1', '1.14', '1.13.2', '1.13.1', '1.13', '1.12.2', '1.12.1', '1.12',
                '1.11.2', '1.11.1', '1.11', '1.10.2', '1.10.1', '1.10', '1.9.4', '1.9.3', '1.9.2', '1.9.1',
                '1.9', '1.8.9', '1.8.8', '1.8.7', '1.8.6', '1.8.5', '1.8.4', '1.8.3', '1.8.2', '1.8.1', '1.8', '1.7.10'],

    'spigot': ['26.1.2', '26.1.1', '26.1', '1.21.11', '1.21.10', '1.21.8', '1.21.5', '1.21.4','1.21.3', '1.21.1', '1.20.6', '1.20.4',
               '1.20.2', '1.20.1', '1.19.4', '1.19.3', '1.19.2', '1.19.1', '1.19', '1.18.2', '1.18.1', '1.18', '1.16.5',
               '1.16.4', '1.16.3', '1.16.2', '1.16.1', '1.15.2', '1.15.1', '1.15', '1.14.4', '1.14.3', '1.14.2', '1.14.1',
               '1.14', '1.13.2', '1.13.1', '1.13', '1.12.2', '1.12.1', '1.12', '1.11.2', '1.11', '1.10.2', '1.9.4', '1.9.2',
               '1.9', '1.8.8', '1.8.3', '1.8'],

    'paper': ['26.2', '26.1.2', '26.1.1', '26.1', '1.21.11', '1.21.10', '1.21.9', '1.21.8', '1.21.7', '1.21.6',
              '1.21.5', '1.21.4', '1.21.3', '1.21.1', '1.21', '1.20.6', '1.20.5', '1.20.4', '1.20.2',
              '1.20.1', '1.20', '1.19.4', '1.19.3', '1.19.2', '1.19.1', '1.19', '1.18.2', '1.18.1', '1.18',
              '1.17.1', '1.17', '1.16.5', '1.16.4', '1.16.3', '1.16.2', '1.16.1', '1.15.2', '1.15.1', '1.15',
              '1.14.4', '1.14.3', '1.14.2', '1.14.1', '1.14', '1.13.2', '1.13.1', '1.13', '1.12.2', '1.12.1',
              '1.12','1.11.2','1.10.2','1.9.4','1.8.8','1.7.10'],

    'velocity':['Lastest'],

    'bungee':['Lastest 1.7 - 1.20'],

    'mohist':['1.20.2','1.20.1','1.18.2','1.16.5','1.12.2'],

    'foila':['26.1.2', '1.21.11', '1.21.8', '1.21.6', '1.21.5', '1.21.4', '1.20.6', '1.20.4', '1.20.2', '1.20.1', '1.19.4'],

    'purpur':['26.2', '26.1.2', '1.21.11', '1.21.10', '1.21.9', '1.21.8', '1.21.7', '1.21.6', '1.21.5', '1.21.4', '1.21.3',
              '1.21.1', '1.21', '1.20.6', '1.20.4', '1.20.2', '1.20.1', '1.20', '1.19.4', '1.19.3', '1.19.2', '1.19.1',
              '1.19', '1.18.2', '1.18.1', '1.18', '1.17.1', '1.17', '1.16.5', '1.16.4', '1.16.3', '1.16.2', '1.16.1',
              '1.15.2', '1.15.1', '1.15', '1.14.4', '1.14.3', '1.14.2', '1.14.1']
}

# -----------------------------------------------
# Сопоставление версий Minecraft и рекомендуемых версий Java
# -----------------------------------------------
JAVA_VERSION_MAP = [
    ('1.20.5', 21),  # Mojang обновили требование до Java 21
    ('1.17', 17),    # Переход на Java 17
    ('1.12.2', 8),   # Последняя версия для Java 8
]

def get_recommended_java(mc_version):
    """
    Определяет рекомендуемую версию Java для указанной версии Minecraft.
    
    Args:
        mc_version: строка версии Minecraft (например, '1.20.4', '1.19.4', '1.16.5')
    
    Returns:
        dict: {'java_version': int, 'java_path': str, 'recommendation': str}
    """
    try:
        # Парсим версию Minecraft
        version_parts = mc_version.split('.')
        if len(version_parts) < 2:
            raise ValueError(f'Неверный формат версии: {mc_version}')
        
        major = int(version_parts[1])
        minor = int(version_parts[2]) if len(version_parts) > 2 else 0
        
        # Определяем версию Java
        if (major, minor) >= (20, 5):
            java_version = 21
            java_path = '/usr/lib/jvm/java-21-openjdk-amd64/bin/java'
            recommendation = 'Java 21 (обязательно для Minecraft 1.20.5+)'
        elif (major, minor) >= (17, 0):
            java_version = 17
            java_path = '/usr/lib/jvm/java-17-openjdk-amd64/bin/java'
            recommendation = 'Java 17 (требуется для Minecraft 1.17-1.20.4)'
        elif (major, minor) >= (13, 0):
            java_version = 11
            java_path = '/usr/lib/jvm/java-11-openjdk-amd64/bin/java'
            recommendation = 'Java 11 (рекомендуется для Minecraft 1.13-1.16.5)'
        else:
            java_version = 8
            java_path = '/usr/lib/jvm/java-1.8.0-openjdk-amd64/bin/java'
            recommendation = 'Java 8 (требуется для Minecraft 1.12.2 и ниже)'
        
        logger.debug(f'Для Minecraft {mc_version} рекомендована {recommendation}')
        
        return {
            'java_version': java_version,
            'java_path': java_path,
            'recommendation': recommendation
        }
    except Exception as e:
        logger.error(f'Ошибка определения версии Java для {mc_version}: {str(e)}')
        return {
            'java_version': 8,
            'java_path': 'java',
            'recommendation': 'Java 8 (по умолчанию)'
        }

# ------------------------------------------------------------
# Инициализация приложения
# ------------------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

# Кэш и сжатие
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
compress = Compress(app)

# SocketIO с WebSocket для real-time консоли
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60, ping_interval=25)
logger.info('Lavaferret Minecraft Panel запущен с async_mode=threading (WebSocket)')

# Фильтр для шаблонов
@app.template_filter('dirname')
def dirname_filter(path):
    if not path:
        return ''
    return '/'.join(path.split('/')[:-1])

@app.context_processor
def inject_csrf_token():
    """Добавляет csrf_token в шаблоны без Flask-WTF"""
    from flask import session
    return dict(csrf_token=session.get('_csrf_token', ''))

# БД
db.init_app(app)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_server_or_404(server_id):
    server = db.session.get(Server, server_id)
    if not server:
        abort(404)
    if server.user_id == current_user.id or current_user in server.co_owners:
        return server
    abort(403)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Создание таблиц и настройка БД
with app.app_context():
    db.create_all()
    db.session.execute(text("PRAGMA journal_mode=WAL"))
    
    # Миграция: добавление полей если их нет
    try:
        columns = [row[1] for row in db.session.execute(text("PRAGMA table_info(server)")).fetchall()]
        if 'java_version' not in columns:
            db.session.execute(text("ALTER TABLE server ADD COLUMN java_version INTEGER"))
            logger.info('Добавлено поле java_version в таблицу server')
        if 'memory_mb' not in columns:
            db.session.execute(text("ALTER TABLE server ADD COLUMN memory_mb INTEGER DEFAULT 4096"))
            logger.info('Добавлено поле memory_mb в таблицу server')
        
        # Фиксим неправильные пути к Java у существующих серверов
        servers = Server.query.all()
        fixed_count = 0
        for server in servers:
            if server.java_path and 'java-21-openjdk/bin/java' in server.java_path and 'amd64' not in server.java_path:
                server.java_path = '/usr/lib/jvm/java-21-openjdk-amd64/bin/java'
                fixed_count += 1
                logger.info(f'Исправлен путь к Java для сервера {server.name}: {server.java_path}')
            if server.java_path and 'java-17-openjdk/bin/java' in server.java_path and 'amd64' not in server.java_path:
                server.java_path = '/usr/lib/jvm/java-17-openjdk-amd64/bin/java'
                fixed_count += 1
                logger.info(f'Исправлен путь к Java для сервера {server.name}: {server.java_path}')
        
        if fixed_count > 0:
            db.session.commit()
            logger.info(f'Исправлено {fixed_count} путей к Java')
        
        db.session.commit()
    except Exception as e:
        logger.warning(f'Ошибка при миграции БД (игнорируется): {str(e)}')
        db.session.rollback()

# Фоновый апдейтер (отключён – можно включить при необходимости)
from status_updater import StatusUpdater
updater = StatusUpdater(app, interval=60)
updater.start()

# ------------------------------------------------------------
# Роуты авторизации
# ------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            logger.warning(f'Registration attempt with existing username: {username}')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed)
        db.session.add(user)
        db.session.commit()
        logger.info(f'New user registered: {username}')
        flash('Registration successful, please login')
        return redirect(url_for('login'))
    from flask import session
    import secrets
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            from flask import session
            import secrets
            if '_csrf_token' not in session:
                session['_csrf_token'] = secrets.token_hex(32)
            logger.info(f'User logged in: {username}')
            return redirect(url_for('index'))
        flash('Invalid credentials')
        logger.warning(f'Failed login attempt for username: {username}')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logger.info(f'User logged out: {current_user.username}')
    logout_user()
    return redirect(url_for('login'))

# ------------------------------------------------------------
# Основные страницы
# ------------------------------------------------------------
@app.route('/')
@login_required
def index():
    from flask import session
    import secrets
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    own_servers = Server.query.filter_by(user_id=current_user.id).all()
    co_servers = Server.query.join(server_access).filter(server_access.c.user_id == current_user.id).all()
    servers = list(set(own_servers + co_servers))

    stats_list = []
    for server in servers:
        try:
            client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
            status = get_status(client, server.name)
            if server.status != status:
                server.status = status
            stats = get_system_stats(client)
            stats_list.append(stats)
            client.close()
        except Exception:
            server.status = 'offline'
            stats_list.append({'cpu_percent': 0, 'ram_total_mb': 0, 'ram_used_mb': 0, 'ram_percent': 0})
    db.session.commit()

    server_stats = zip(servers, stats_list)
    return render_template('index.html', server_stats=server_stats)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_server():
    if request.method == 'POST':
        name = request.form['name']
        host = request.form['host']
        port = int(request.form['port'])
        user = request.form['user']
        password = request.form['password']
        server_type = request.form['server_type']
        version = request.form['version']

        existing = Server.query.filter_by(name=name, user_id=current_user.id).first()
        if existing:
            flash('Server name already exists for your account')
            logger.warning(f'User {current_user.username} tried to add server with existing name: {name}')
            return redirect(url_for('add_server'))

        try:
            logger.info(f'User {current_user.username} deploying new server: {name} (type={server_type}, version={version})')
            client = ssh_connect(host, port, user, password)
            deploy_minecraft_server(client, name, server_type, version, password, memory_mb=4096)
            client.close()

            server = Server(
                name=name,
                ssh_host=host,
                ssh_port=port,
                ssh_user=user,
                server_type=server_type,
                mc_version=version,
                user_id=current_user.id,
                status='running',
                memory_mb=4096  # 4 ГБ по умолчанию
            )
            server.set_password(password)
            
            # Автоматический подбор Java версии
            java_info = get_recommended_java(version)
            server.java_path = java_info['java_path']
            server.java_version = java_info['java_version']
            logger.info(f'Автоматически подобрана Java {java_info["java_version"]} для Minecraft {version}')
            
            db.session.add(server)
            db.session.commit()
            cache.delete('index')
            logger.info(f'Server deployed successfully: {name}')
            flash('Server deployed successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f'Failed to deploy server {name}: {str(e)}')
            flash(f'Error: {str(e)}')
            return redirect(url_for('add_server'))
    return render_template('add_server.html', versions=versions)

@app.route('/server/<int:server_id>')
@login_required
def server_detail(server_id):
    server = get_server_or_404(server_id)
    logs = ''
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        logs = get_logs(client, server.name)
        status = get_status(client, server.name)
        server.status = status
        db.session.commit()
        client.close()
    except Exception as e:
        logs = f"Could not fetch logs: {e}"
        server.status = 'offline'
        db.session.commit()
    return render_template('server_detail.html', server=server, logs=logs)

@app.route('/api/server/<int:server_id>/stats')
@login_required
def api_server_stats(server_id):
    server = get_server_or_404(server_id)
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        stats = get_system_stats(client)
        client.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'cpu_percent': 0.0, 'ram_total_mb': 0, 'ram_used_mb': 0, 'ram_percent': 0.0, 'error': str(e)})

@app.route('/api/host/stats')
@login_required
def api_host_stats():
    """
    Получает статистику всех SSH хостов
    Группирует серверы по хостам и возвращает одну статистику на хост
    """
    own_servers = Server.query.filter_by(user_id=current_user.id).all()
    co_servers = Server.query.join(server_access).filter(server_access.c.user_id == current_user.id).all()
    servers = list(set(own_servers + co_servers))
    
    # Группируем серверы по хостам
    hosts = {}
    for server in servers:
        host_key = f"{server.ssh_host}:{server.ssh_port}"
        if host_key not in hosts:
            hosts[host_key] = {
                'host': server.ssh_host,
                'port': server.ssh_port,
                'user': server.ssh_user,
                'password': server.get_password(),
                'servers': []
            }
        hosts[host_key]['servers'].append({
            'id': server.id,
            'name': server.name,
            'status': server.status
        })
    
    # Получаем статистику для каждого хоста
    result = []
    for host_key, host_data in hosts.items():
        try:
            client = ssh_connect(host_data['host'], host_data['port'], host_data['user'], host_data['password'])
            stats = get_host_system_stats(client)
            client.close()
            
            stats['host'] = host_data['host']
            stats['port'] = host_data['port']
            stats['user'] = host_data['user']
            stats['servers'] = host_data['servers']
            stats['server_count'] = len(host_data['servers'])
            
            logger.info(f'[HOST_STATS API] Host {host_key}: ram_total={stats.get("ram_total_mb", 0)}MB, ram_used={stats.get("ram_used_mb", 0)}MB, ram_percent={stats.get("ram_percent", 0)}%')
            
            result.append(stats)
        except Exception as e:
            logger.error(f'Ошибка получения статистики хоста {host_key}: {str(e)}')
            result.append({
                'host': host_data['host'],
                'port': host_data['port'],
                'user': host_data['user'],
                'servers': host_data['servers'],
                'server_count': len(host_data['servers']),
                'error': str(e)
            })
    
    return jsonify({'hosts': result})

@cache.memoize(timeout=5)
def get_console_cached(server_id, server):
    client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
    console = get_console_output(client, server.name)
    client.close()
    return console

@app.route('/server/<int:server_id>/api/logs')
@login_required
def api_get_logs(server_id):
    try:
        server = get_server_or_404(server_id)
        console = get_console_cached(server_id, server)
        return jsonify({'logs': console})
    except Exception as e:
        return jsonify({'logs': f'Error: {str(e)}'}), 500

@app.route('/server/<int:server_id>/api/live-console')
@login_required
def api_get_live_console(server_id):
    """Получает live статус сервера через RCON"""
    try:
        server = get_server_or_404(server_id)
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        live_data = get_live_console(client, server.name)
        client.close()
        return jsonify({'live': live_data})
    except Exception as e:
        return jsonify({'live': f'Error: {str(e)}'}), 500

# ------------------------------------------------------------
# Управление сервером (start, stop, restart, delete)
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/start')
@login_required
def start_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        logger.info(f'User {current_user.username} starting server: {server.name}')
        password = server.get_password()
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, password)
        start_server_via_nohup(client, server.name, password, server.java_path if hasattr(server, 'java_path') else "java")
        client.close()
        server.status = 'running'
        db.session.commit()
        cache.delete('index')
        logger.info(f'Server started: {server.name}')
        flash('Server started')
    except Exception as e:
        logger.error(f'Failed to start server {server.name}: {str(e)}')
        flash(f'Error: {e}')
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/server/<int:server_id>/stop')
@login_required
def stop_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        logger.info(f'User {current_user.username} stopping server: {server.name}')
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        stop_server(client, server.name)
        client.close()
        server.status = 'stopped'
        db.session.commit()
        cache.delete('index')
        logger.info(f'Server stopped: {server.name}')
        flash('Server stopped')
    except Exception as e:
        logger.error(f'Failed to stop server {server.name}: {str(e)}')
        flash(f'Error: {e}')
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/server/<int:server_id>/restart')
@login_required
def restart_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        logger.info(f'User {current_user.username} restarting server: {server.name}')
        password = server.get_password()
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, password)
        restart_server(client, server.name, password, server.java_path if hasattr(server, 'java_path') else "java")
        client.close()
        server.status = 'running'
        db.session.commit()
        cache.delete('index')
        logger.info(f'Server restarted: {server.name}')
        flash('Server restarted')
    except Exception as e:
        logger.error(f'Failed to restart server {server.name}: {str(e)}')
        flash(f'Error restarting: {e}')
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/server/<int:server_id>/delete', methods=['POST'])
@login_required
def delete_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        logger.info(f'User {current_user.username} deleting server: {server.name}')
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        delete_server(client, server.name)
        client.close()
        db.session.delete(server)
        db.session.commit()
        cache.delete('index')
        logger.info(f'Server deleted: {server.name}')
        flash('Server deleted')
    except Exception as e:
        logger.error(f'Failed to delete server {server.name}: {str(e)}')
        flash(f'Error: {e}')
    return redirect(url_for('index'))

# ------------------------------------------------------------
# API для консоли (AJAX)
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/api/command', methods=['POST'])
@login_required
def api_send_command(server_id):
    server = get_server_or_404(server_id)
    command = request.json.get('command')
    if not command:
        return jsonify({'status': 'error', 'message': 'No command'}), 400
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        send_command(client, server.name, command)
        client.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ------------------------------------------------------------
# Страница консоли
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/console')
@login_required
def console(server_id):
    server = get_server_or_404(server_id)
    return render_template('console.html', server=server, active_page='console')

# ------------------------------------------------------------
# SSH настройки
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/ssh-settings', methods=['GET', 'POST'])
@login_required
def ssh_settings(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        new_host = request.form.get('ssh_host')
        new_port = request.form.get('ssh_port')
        new_user = request.form.get('ssh_user')
        if new_host:
            server.ssh_host = new_host
        if new_port:
            server.ssh_port = int(new_port)
        if new_user:
            server.ssh_user = new_user
        db.session.commit()
        flash('SSH настройки обновлены')
        return redirect(url_for('ssh_settings', server_id=server.id))
    return render_template('ssh_settings.html', server=server, active_page='ssh_settings')

# ------------------------------------------------------------
# Разделы панели (игроки, файлы, конфиг, плагины, моды, бэкапы, порты, домен, строка запуска, настройки, совладельцы, смена ядра)
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/players')
@login_required
def players(server_id):
    server = get_server_or_404(server_id)
    ops = []
    whitelist = []
    bans = []
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        for fname, lst in [('ops.json', ops), ('whitelist.json', whitelist), ('banned-players.json', bans)]:
            content = get_file_content(client, server.name, fname)
            if content:
                try:
                    data = json.loads(content)
                    lst.extend(data)
                except:
                    pass
        client.close()
    except Exception as e:
        flash(f"Ошибка чтения списков: {e}")
    return render_template('players.html', server=server, ops=ops, whitelist=whitelist, bans=bans, active_page='players')

@app.route('/server/<int:server_id>/files/edit', methods=['GET', 'POST'])
@login_required
def edit_file(server_id):
    server = get_server_or_404(server_id)
    file_path = request.args.get('path', '')
    if not file_path:
        abort(400)

    if request.method == 'POST':
        content = request.form.get('content')
        if content is None:
            abort(400)
        try:
            client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
            # Записываем с явной кодировкой UTF-8
            write_file_content(client, server.name, file_path, content)
            client.close()
            flash('Файл сохранён')
        except Exception as e:
            flash(f'Ошибка сохранения: {e}')
        return redirect(url_for('files', server_id=server.id, path='/'.join(file_path.split('/')[:-1]) if '/' in file_path else ''))

    # GET: читаем содержимое файла
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        # Читаем с UTF-8
        content = get_file_content(client, server.name, file_path)
        client.close()
        if content is None:
            flash('Файл не найден')
            return redirect(url_for('files', server_id=server.id))
        return render_template('edit_file.html', server=server, file_path=file_path, content=content)
    except Exception as e:
        flash(f'Ошибка чтения: {e}')
        return redirect(url_for('files', server_id=server.id))

@app.route('/server/<int:server_id>/files/delete', methods=['POST'])
@login_required
def delete_file_route(server_id):
    """Удаление файла через веб-интерфейс"""
    server = get_server_or_404(server_id)
    file_path = request.args.get('file')
    if not file_path:
        abort(400)
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        # Вызываем delete_file из ssh_utils через полное имя
        from ssh_utils import delete_file as ssh_delete_file
        ssh_delete_file(client, server.name, file_path)
        client.close()
        return '', 200
    except Exception as e:
        return str(e), 500

@app.route('/server/<int:server_id>/files', methods=['GET', 'POST'])
@login_required
def files(server_id):
    server = get_server_or_404(server_id)
    path = request.args.get('path', '')
    if request.method == 'POST':
        if 'file' in request.files:
            f = request.files['file']
            if f.filename:
                logger.info(f'Uploading file: {f.filename} to path: {path}')
                # Читаем как байты - работает для любых файлов
                content_bytes = f.read()
                try:
                    client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                    target_path = path + '/' + f.filename if path else f.filename
                    logger.info(f'Writing to: {target_path} ({len(content_bytes)} bytes)')
                    write_file_content_binary(client, server.name, target_path, content_bytes)
                    client.close()
                    logger.info(f'File uploaded successfully: {f.filename}')
                    flash('Файл загружен')
                except Exception as e:
                    logger.error(f'File upload error: {str(e)}')
                    flash(f'Ошибка: {e}')
        if 'new_dir' in request.form:
            dirname = request.form['new_dir']
            try:
                client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                create_directory(client, server.name, path + '/' + dirname if path else dirname)
                client.close()
                flash('Директория создана')
            except Exception as e:
                flash(f'Ошибка: {e}')
        return redirect(url_for('files', server_id=server.id, path=path))
    file_list = []
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        file_list = list_files(client, server.name, path)
        client.close()
    except Exception as e:
        flash(f'Ошибка получения списка: {e}')
    return render_template('files.html', server=server, files=file_list, path=path, active_page='files')

@app.route('/server/<int:server_id>/files/download')
@login_required
def download_file(server_id):
    server = get_server_or_404(server_id)
    file_path = request.args.get('file')
    if not file_path:
        abort(400)
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        content = get_file_content(client, server.name, file_path)
        client.close()
        if content is None:
            flash('Файл не найден')
            return redirect(url_for('files', server_id=server.id))
        return Response(content, mimetype='application/octet-stream', headers={"Content-Disposition": f"attachment;filename={file_path.split('/')[-1]}"})
    except Exception as e:
        flash(f'Ошибка: {e}')
        return redirect(url_for('files', server_id=server.id))

@app.route('/server/<int:server_id>/config', methods=['GET', 'POST'])
@login_required
def config(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        try:
            client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
            props = {}
            for key, value in request.form.items():
                if key.startswith('prop_'):
                    real_key = key[5:]
                    props[real_key] = value
            write_server_properties(client, server.name, props)
            client.close()
            flash('Конфиг обновлён')
        except Exception as e:
            flash(f'Ошибка: {e}')
        return redirect(url_for('config', server_id=server.id))
    props = {}
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        props = read_server_properties(client, server.name)
        client.close()
    except Exception as e:
        flash(f'Не удалось прочитать конфиг: {e}')
    return render_template('config.html', server=server, props=props, active_page='config')

@app.route('/server/<int:server_id>/plugins', methods=['GET', 'POST'])
@login_required
def plugins(server_id):
    server = get_server_or_404(server_id)
    installed_plugins = []
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        plugins_dir = f"/home/{server.ssh_user}/minecraft_servers/{server.name}/plugins"
        out, err, code = execute_command(client, f"ls -la {plugins_dir}")
        if code == 0:
            for line in out.split('\n'):
                if '.jar' in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        installed_plugins.append(parts[8])
        client.close()
    except Exception as e:
        flash(f'Ошибка: {e}')
    if request.method == 'POST':
        plugin_url = request.form.get('plugin_url')
        plugin_name = request.form.get('plugin_name')
        if plugin_url and plugin_name:
            try:
                client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                install_plugin(client, server.name, plugin_url, plugin_name)
                client.close()
                flash('Плагин установлен')
            except Exception as e:
                flash(f'Ошибка: {e}')
        return redirect(url_for('plugins', server_id=server.id))
    return render_template('plugins.html', server=server, installed_plugins=installed_plugins, active_page='plugins')

@app.route('/server/<int:server_id>/plugins/delete', methods=['POST'])
@login_required
def delete_plugin(server_id):
    server = get_server_or_404(server_id)
    file_path = request.args.get('file')
    if not file_path:
        return jsonify({'error': 'Missing file parameter'}), 400
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        plugins_dir = f"/home/{server.ssh_user}/minecraft_servers/{server.name}/plugins"
        full_path = f"{plugins_dir}/{file_path}"
        execute_command(client, f"rm -f {full_path}")
        client.close()
        logger.info(f'Deleted plugin {file_path} from {server.name}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error deleting plugin: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/server/<int:server_id>/mods')
@login_required
def mods(server_id):
    server = get_server_or_404(server_id)
    installed_mods = []
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        mods_dir = f"/home/{server.ssh_user}/minecraft_servers/{server.name}/mods"
        out, err, code = execute_command(client, f"ls -la {mods_dir}")
        if code == 0:
            for line in out.split('\n'):
                if '.jar' in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        installed_mods.append(parts[8])
        client.close()
    except Exception as e:
        flash(f'Ошибка: {e}')
    return render_template('mods.html', server=server, installed_mods=installed_mods, active_page='mods')

@app.route('/server/<int:server_id>/mods/delete', methods=['POST'])
@login_required
def delete_mod(server_id):
    server = get_server_or_404(server_id)
    file_path = request.args.get('file')
    if not file_path:
        return jsonify({'error': 'Missing file parameter'}), 400
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        mods_dir = f"/home/{server.ssh_user}/minecraft_servers/{server.name}/mods"
        full_path = f"{mods_dir}/{file_path}"
        execute_command(client, f"rm -f {full_path}")
        client.close()
        logger.info(f'Deleted mod {file_path} from {server.name}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error deleting mod: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/server/<int:server_id>/backups', methods=['GET', 'POST'])
@login_required
def backups(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        if 'create' in request.form:
            try:
                client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                backup_file = create_backup(client, server.name)
                client.close()
                if backup_file:
                    flash(f'Бэкап создан: {backup_file}')
                else:
                    flash('Ошибка создания бэкапа')
            except Exception as e:
                flash(f'Ошибка: {e}')
        elif 'restore' in request.form:
            backup_name = request.form.get('backup_name')
            if backup_name:
                try:
                    client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                    restore_backup(client, server.name, backup_name)
                    client.close()
                    flash('Бэкап восстановлен')
                except Exception as e:
                    flash(f'Ошибка: {e}')
        return redirect(url_for('backups', server_id=server.id))
    backups_list = []
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        backups_list = list_backups(client, server.name)
        client.close()
    except Exception as e:
        flash(f'Ошибка: {e}')
    return render_template('backups.html', server=server, backups=backups_list, active_page='backups')

@app.route('/server/<int:server_id>/ports', methods=['GET', 'POST'])
@login_required
def ports(server_id):
    server = get_server_or_404(server_id)
    port = 25565
    server_ip = ''
    free_ports = []
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        props = read_server_properties(client, server.name)
        port = int(props.get('server-port', 25565))
        server_ip = props.get('server-ip', '')
        # Собираем свободные порты для отображения
        for p in range(25565, 25585):
            if is_port_free(client, p):
                free_ports.append(p)
        client.close()
    except Exception as e:
        flash(f'Ошибка чтения: {e}')
    if request.method == 'POST':
        new_port = request.form.get('port')
        new_ip = request.form.get('server_ip')
        try:
            client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
            props = read_server_properties(client, server.name)
            if new_port:
                props['server-port'] = new_port
            if new_ip is not None:
                props['server-ip'] = new_ip
            write_server_properties(client, server.name, props)
            client.close()
            flash('Порт и IP обновлены (требуется перезапуск сервера)')
        except Exception as e:
            flash(f'Ошибка: {e}')
        return redirect(url_for('ports', server_id=server.id))
    return render_template('ports.html', server=server, port=port, server_ip=server_ip, free_ports=free_ports, active_page='ports')

# ------------------------------------------------------------
# SSH туннелирование портов
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/tunnel/start', methods=['POST'])
@login_required
def start_tunnel(server_id):
    server = get_server_or_404(server_id)
    try:
        result = create_ssh_tunnel(
            server_name=server.name,
            ssh_host=server.ssh_host,
            ssh_port=server.ssh_port,
            ssh_user=server.ssh_user,
            ssh_password=server.get_password(),
            remote_port=25565,
            local_port=0  # Автоматический выбор
        )
        
        if result['success']:
            logger.info(f'User {current_user.username} started tunnel for {server.name}: {result["connect_string"]}')
            return jsonify({
                'success': True,
                'local_port': result['local_port'],
                'connect_string': result['connect_string']
            })
        else:
            logger.error(f'Failed to start tunnel for {server.name}: {result.get("error")}')
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
            
    except Exception as e:
        logger.error(f'Tunnel start error for {server.name}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/server/<int:server_id>/tunnel/stop', methods=['POST'])
@login_required
def stop_tunnel(server_id):
    server = get_server_or_404(server_id)
    try:
        result = close_ssh_tunnel(server.name)
        
        if result['success']:
            logger.info(f'User {current_user.username} stopped tunnel for {server.name}')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
            
    except Exception as e:
        logger.error(f'Tunnel stop error for {server.name}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/server/<int:server_id>/tunnel/status')
@login_required
def tunnel_status(server_id):
    server = get_server_or_404(server_id)
    try:
        status = get_tunnel_status(server.name)
        return jsonify(status)
    except Exception as e:
        return jsonify({'active': False, 'error': str(e)}), 500

# ------------------------------------------------------------
# Cloudflare DNS и Tunnel
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/cloudflare/test-config')
@login_required
def test_cloudflare_config(server_id):
    """Проверяет конфигурацию Cloudflare API"""
    result = {
        'configured': all([Config.CLOUDFLARE_API_KEY, Config.CLOUDFLARE_EMAIL, Config.CLOUDFLARE_ZONE_ID, Config.CLOUDFLARE_DOMAIN]),
        'api_key_set': bool(Config.CLOUDFLARE_API_KEY),
        'email_set': bool(Config.CLOUDFLARE_EMAIL),
        'zone_id_set': bool(Config.CLOUDFLARE_ZONE_ID),
        'domain_set': bool(Config.CLOUDFLARE_DOMAIN),
        'zone_id': Config.CLOUDFLARE_ZONE_ID,
        'domain': Config.CLOUDFLARE_DOMAIN
    }
    
    # Пробуем сделать запрос к API
    if result['configured']:
        test_result = cloudflare_api_request('GET', '/')
        result['api_working'] = test_result.get('success', False)
        if not test_result.get('success'):
            result['api_error'] = test_result.get('error', 'Unknown')
    else:
        result['api_working'] = False
        result['api_error'] = 'API credentials not configured'
    
    return jsonify(result)

@app.route('/server/<int:server_id>/cloudflare/setup', methods=['POST'])
@login_required
def setup_cloudflare(server_id):
    server = get_server_or_404(server_id)
    try:
        # Создаём DNS запись
        dns_result = create_cloudflare_dns(server.name)
        if not dns_result['success']:
            return jsonify({'success': False, 'error': dns_result['error']}), 400
        
        # Подключаемся к серверу и настраиваем cloudflared
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        
        # Получаем порты сервера
        ports = get_server_ports_from_properties(
            server.ssh_host, server.ssh_port, 
            server.ssh_user, server.get_password(), 
            server.name
        )
        
        if not ports:
            ports = [
                {'port': 25565, 'service': 'Minecraft'},
                {'port': 25575, 'service': 'RCON'},
                {'port': 25566, 'service': 'Query'},
            ]
        
        # Создаём список локальных портов (все 0 для автовыбора)
        local_ports = [(p['port'], 0) for p in ports]
        
        # Настраиваем cloudflared
        setup_result = setup_cloudflared_on_server(client, server.name, server.ssh_user, local_ports)
        if not setup_result['success']:
            client.close()
            error_msg = setup_result.get('error', 'Unknown error')
            # Показываем более понятное сообщение
            if 'API Error' in error_msg or 'authentication' in error_msg.lower():
                error_msg = 'Ошибка аутентификации Cloudflare API. Проверьте API Key и Token в настройках.'
            elif 'credentials' in error_msg.lower():
                error_msg = 'Не удалось создать credentials tunnel. Проверьте права API Token.'
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Сохраняем поддомен в базе
        server.domain = dns_result['subdomain']
        db.session.commit()
        
        client.close()
        
        logger.info(f'User {current_user.username} setup Cloudflare for {server.name}: {dns_result["subdomain"]}')
        
        return jsonify({
            'success': True,
            'subdomain': dns_result['subdomain'],
            'tunnel_dir': setup_result['tunnel_dir'],
            'tunnel_name': setup_result.get('tunnel_name', '')
        }), 200
        
    except Exception as e:
        logger.error(f'Cloudflare setup error for {server.name}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/server/<int:server_id>/cloudflare/start', methods=['POST'])
@login_required
def start_cloudflare_tunnel(server_id):
    server = get_server_or_404(server_id)
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        result = start_cloudflared_tunnel(client, server.name, server.ssh_user)
        client.close()
        
        if result['success']:
            logger.info(f'User {current_user.username} started Cloudflare tunnel for {server.name}')
            return jsonify({'success': True, 'log': result.get('log', '')})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
            
    except Exception as e:
        logger.error(f'Cloudflare start error for {server.name}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/server/<int:server_id>/cloudflare/stop', methods=['POST'])
@login_required
def stop_cloudflare_tunnel(server_id):
    server = get_server_or_404(server_id)
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        result = stop_cloudflared_tunnel(client, server.name, server.ssh_user)
        client.close()
        
        if result['success']:
            logger.info(f'User {current_user.username} stopped Cloudflare tunnel for {server.name}')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
            
    except Exception as e:
        logger.error(f'Cloudflare stop error for {server.name}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/server/<int:server_id>/cloudflare/status')
@login_required
def cloudflare_tunnel_status(server_id):
    server = get_server_or_404(server_id)
    try:
        # Проверяем DNS запись
        subdomain = server.name.lower().replace(' ', '-')
        dns_status = get_cloudflare_dns(subdomain)
        
        # Проверяем запущен ли tunnel на сервере
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        out, err, code = execute_command(client, "pgrep -f 'cloudflared tunnel'", timeout=5)
        tunnel_running = code == 0 and out.strip()
        client.close()
        
        return jsonify({
            'dns_configured': dns_status.get('exists', False),
            'subdomain': f"{subdomain}.{Config.CLOUDFLARE_DOMAIN}" if Config.CLOUDFLARE_DOMAIN else '',
            'tunnel_running': tunnel_running
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/server/<int:server_id>/cloudflare/delete', methods=['POST'])
@login_required
def delete_cloudflare(server_id):
    server = get_server_or_404(server_id)
    try:
        # Останавливаем tunnel
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        stop_cloudflared_tunnel(client, server.name, server.ssh_user)
        client.close()
        
        # Удаляем DNS запись
        dns_result = delete_cloudflare_dns(server.name)
        
        # Очищаем domain в базе
        server.domain = None
        db.session.commit()
        
        logger.info(f'User {current_user.username} deleted Cloudflare config for {server.name}')
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f'Cloudflare delete error for {server.name}: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/server/<int:server_id>/domain', methods=['GET', 'POST'])
@login_required
def domain(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        domain_name = request.form.get('domain')
        if domain_name:
            server.domain = domain_name
            db.session.commit()
            flash('Домен сохранён')
        return redirect(url_for('domain', server_id=server.id))
    return render_template('domain.html', server=server, active_page='domain')

@app.route('/server/<int:server_id>/startup', methods=['GET', 'POST'])
@login_required
def startup(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        server.startup_command = request.form.get('startup_command', server.startup_command)
        server.memory_mb = int(request.form.get('memory_mb', server.memory_mb))
        server.timezone = request.form.get('timezone', server.timezone)
        server.garbage_collector = request.form.get('garbage_collector', server.garbage_collector)
        server.java_path = request.form.get('java_path', server.java_path if hasattr(server, 'java_path') else 'java')
        db.session.commit()
        flash('Строка запуска обновлена')
        return redirect(url_for('startup', server_id=server.id))
    return render_template('startup.html', server=server, active_page='startup')

@app.route('/server/<int:server_id>/settings', methods=['GET', 'POST'])
@login_required
def settings(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        flash('Настройки сохранены (заглушка)')
        return redirect(url_for('settings', server_id=server.id))
    return render_template('settings.html', server=server, active_page='settings')

@app.route('/server/<int:server_id>/coowners', methods=['GET', 'POST'])
@login_required
def coowners(server_id):
    # Только владелец может управлять совладельцами
    server = Server.query.filter_by(id=server_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        if action == 'add' and username:
            user = User.query.filter_by(username=username).first()
            if user:
                if user not in server.co_owners:
                    server.co_owners.append(user)
                    db.session.commit()
                    flash(f'Совладелец {username} добавлен')
                else:
                    flash(f'Пользователь {username} уже является совладельцем')
            else:
                flash(f'Пользователь {username} не найден')
        elif action == 'remove' and username:
            user = User.query.filter_by(username=username).first()
            if user and user in server.co_owners:
                server.co_owners.remove(user)
                db.session.commit()
                flash(f'Совладелец {username} удалён')
            else:
                flash(f'Пользователь {username} не является совладельцем')
        return redirect(url_for('coowners', server_id=server.id))
    coowners_list = server.co_owners.all()
    return render_template('coowners.html', server=server, coowners=coowners_list, active_page='coowners')

@app.route('/server/<int:server_id>/change-core', methods=['GET', 'POST'])
@login_required
def change_core(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        new_type = request.form.get('server_type')
        new_version = request.form.get('mc_version')
        change_mode = request.form.get('change_mode', 'kernel_only')  # 'kernel_only' или 'full_reset'
        
        if new_type and new_version:
            try:
                client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                
                if change_mode == 'full_reset':
                    logger.info(f'User {current_user.username} doing FULL RESET core change for {server.name}')
                    flash_warning = '⚠️ Будет удалён весь мир, плагины и конфиги (кроме бэкапов)!'
                else:
                    logger.info(f'User {current_user.username} doing kernel-only change for {server.name}')
                    flash_warning = None
                
                # Вызываем новую функцию смены ядра
                change_server_core(
                    client=client,
                    server_name=server.name,
                    new_server_type=new_type,
                    new_mc_version=new_version,
                    password=server.get_password(),
                    memory_mb=server.memory_mb if hasattr(server, 'memory_mb') else 4096,
                    mode=change_mode
                )
                
                server.server_type = new_type
                server.mc_version = new_version
                
                # Обновляем рекомендацию Java при смене версии
                java_info = get_recommended_java(new_version)
                server.java_path = java_info['java_path']
                server.java_version = java_info['java_version']
                logger.info(f'Обновлена Java до {java_info["java_version"]} при смене ядра на {new_type} {new_version}')
                
                db.session.commit()
                
                if change_mode == 'full_reset':
                    flash(f'✅ Полная переустановка завершена! Мир и конфиги удалены. Ядро: {new_type} {new_version}')
                else:
                    flash(f'✅ Ядро изменено на {new_type} {new_version}. Мир и конфиги сохранены.')
                
                if flash_warning:
                    flash(flash_warning, 'warning')
                
                client.close()
            except Exception as e:
                logger.error(f'Core change error: {str(e)}')
                flash(f'Ошибка: {str(e)}')
        return redirect(url_for('change_core', server_id=server.id))
    return render_template('change_core.html', server=server, versions=versions, active_page='change_core')

# ------------------------------------------------------------
# Modrinth API
# ------------------------------------------------------------
@app.route('/api/modrinth/search')
@login_required
def modrinth_search():
    query = request.args.get('query', '')
    project_type = request.args.get('type', 'mod')
    version = request.args.get('version', '')
    loader = request.args.get('loader', '')
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify({'projects': []})

    facets = [[f'project_type:{project_type}']]
    if version:
        facets.append([f'versions:{version}'])
    if loader and project_type == 'mod':
        facets.append([f'categories:{loader}'])

    url = "https://api.modrinth.com/v2/search"
    params = {'query': query, 'limit': limit, 'facets': json.dumps(facets)}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return jsonify({'error': 'Failed to fetch from Modrinth'}), 500
        data = resp.json()
        projects = []
        for hit in data.get('hits', []):
            projects.append({
                'id': hit['project_id'],
                'title': hit['title'],
                'slug': hit.get('slug', ''),
                'description': hit.get('description', ''),
                'icon_url': hit.get('icon_url', ''),
                'downloads': hit.get('downloads', 0),
                'versions': hit.get('versions', []),
                'latest_version': hit.get('latest_version', ''),
                'project_type': hit.get('project_type', ''),
            })
        return jsonify({'projects': projects})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/modrinth/versions/<project_id>')
@login_required
def modrinth_versions(project_id):
    loader_filter = request.args.get('loader', '')
    version_filter = request.args.get('version', '')
    try:
        url = f"https://api.modrinth.com/v2/project/{project_id}/version"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return jsonify({'error': 'Failed to fetch versions'}), 500
        versions_data = resp.json()
        result = []
        for v in versions_data:
            game_versions = v.get('game_versions', [])
            if version_filter and version_filter not in game_versions:
                continue
            if loader_filter and loader_filter not in v.get('loaders', []):
                continue
            result.append({
                'id': v['id'],
                'version_number': v.get('version_number', ''),
                'game_versions': v.get('game_versions', []),
                'loaders': v.get('loaders', []),
                'release_channel': v.get('release_channel', ''),
                'files': v.get('files', [])
            })
        return jsonify({'versions': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/modrinth/install/<int:server_id>', methods=['POST'])
@login_required
def modrinth_install(server_id):
    server = get_server_or_404(server_id)
    data = request.get_json()
    project_id = data.get('project_id')
    version_id = data.get('version_id')
    project_type = data.get('type')
    
    logger.info(f'Installing {project_type} {project_id} v{version_id} to server {server.name}')
    
    if not project_id or not version_id or not project_type:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        filename = install_modrinth_project(client, server.name, project_id, version_id, project_type)
        client.close()
        logger.info(f'Successfully installed {filename} to {server.name}')
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        logger.error(f'Failed to install {project_type} to {server.name}: {str(e)}')
        return jsonify({'error': str(e)}), 500

# ------------------------------------------------------------
# API для подбора Java версии
# ------------------------------------------------------------
@app.route('/api/java/recommend')
@login_required
def api_java_recommend():
    """Возвращает рекомендованную версию Java для указанной версии Minecraft"""
    mc_version = request.args.get('version', '')
    if not mc_version:
        return jsonify({'error': 'Missing version parameter'}), 400
    
    recommendation = get_recommended_java(mc_version)
    logger.info(f'Запрос рекомендации Java для Minecraft {mc_version}: {recommendation["recommendation"]}')
    
    return jsonify({
        'success': True,
        'mc_version': mc_version,
        'java_version': recommendation['java_version'],
        'java_path': recommendation['java_path'],
        'recommendation': recommendation['recommendation']
    })

@app.route('/api/java/install/<int:server_id>', methods=['POST'])
@login_required
def api_java_install(server_id):
    """Устанавливает рекомендованную Java на указанный сервер через SSH"""
    server = get_server_or_404(server_id)
    java_version = request.json.get('java_version', server.java_version)
    
    if not java_version:
        java_info = get_recommended_java(server.mc_version)
        java_version = java_info['java_version']
    
    try:
        logger.info(f'User {current_user.username} installing Java {java_version} on server {server.name}')
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        password = server.get_password()
        
        # Устанавливаем Java
        java_path = ensure_java_installed(client, password, java_version)
        client.close()
        
        # Обновляем путь к Java в базе
        server.java_path = java_path
        server.java_version = java_version
        db.session.commit()
        
        logger.info(f'Java {java_version} successfully installed on server {server.name}: {java_path}')
        
        return jsonify({
            'success': True,
            'java_path': java_path,
            'java_version': java_version,
            'message': f'Java {java_version} успешно установлена'
        })
    except Exception as e:
        logger.error(f'Failed to install Java {java_version} on server {server.name}: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ------------------------------------------------------------
# WebSocket для real-time консоли
# ------------------------------------------------------------
import threading
import time
from flask_socketio import emit, join_room, leave_room

# Хранилище активных WebSocket подключений
console_connections = {}

def stream_console_to_client(server_id, username, password):
    """
    Фоновый поток для стриминга консоли сервера через WebSocket
    Использует tmux capture-pane для получения live вывода
    """
    try:
        client = ssh_connect(server_id['host'], server_id['port'], username, password)
        server_name = server_id['name']
        
        while server_id.get('active', True):
            try:
                console_output = get_console_output(client, server_name, lines=50)
                
                # Отправляем подключённым клиентам
                room_key = f"console_{server_id['id']}"
                if room_key in console_connections:
                    for sid in console_connections[room_key]:
                        try:
                            socketio.emit('console_update', {'data': console_output}, room=sid)
                        except:
                            pass
            except Exception as e:
                logger.error(f'Ошибка стриминга консоли {server_name}: {str(e)}')
            
            time.sleep(2)  # Обновление каждые 2 секунды
        
        client.close()
    except Exception as e:
        logger.error(f'Ошибка подключения к серверу {server_id.get("name")}: {str(e)}')

@socketio.on('connect')
def handle_connect():
    logger.info(f'WebSocket клиент подключился: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    # Удаляем клиента из всех комнат
    rooms_to_remove = [room for room, sids in console_connections.items() if request.sid in sids]
    for room in rooms_to_remove:
        console_connections[room].discard(request.sid)
        if not console_connections[room]:
            del console_connections[room]
    logger.info(f'WebSocket клиент отключился: {request.sid}')

@socketio.on('join_console')
def handle_join_console(data):
    server_id = data.get('server_id')
    room_key = f"console_{server_id}"
    join_room(room_key)
    
    if room_key not in console_connections:
        console_connections[room_key] = set()
    console_connections[room_key].add(request.sid)
    
    logger.info(f'Клиент {request.sid} присоединился к консоли сервера {server_id}')
    
    # Запускаем поток стриминга если ещё не запущен
    if room_key not in [k for k in console_connections.keys()]:
        # Поток будет запущен при первом подключении
        pass

@socketio.on('leave_console')
def handle_leave_console(data):
    server_id = data.get('server_id')
    room_key = f"console_{server_id}"
    leave_room(room_key)
    
    if room_key in console_connections:
        console_connections[room_key].discard(request.sid)
        if not console_connections[room_key]:
            del console_connections[room_key]
    
    logger.info(f'Клиент {request.sid} покинул консоль сервера {server_id}')

@socketio.on('send_command')
def handle_send_command(data):
    server_id = data.get('server_id')
    command = data.get('command')
    
    if not server_id or not command:
        return {'status': 'error', 'message': 'Missing server_id or command'}
    
    try:
        server = db.session.get(Server, server_id)
        if not server:
            return {'status': 'error', 'message': 'Server not found'}
        
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        send_command(client, server.name, command)
        client.close()
        
        return {'status': 'ok'}
    except Exception as e:
        logger.error(f'Ошибка отправки команды: {str(e)}')
        return {'status': 'error', 'message': str(e)}

# ------------------------------------------------------------
# Запуск
# ------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)