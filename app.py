from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response, abort
from models import db, User, Server, server_access
from ssh_utils import *
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room
from flask_caching import Cache
from flask_compress import Compress
import json
import threading
import time
from status_updater import StatusUpdater
import requests
import eventlet
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)

# Кэширование
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Сжатие ответов
compress = Compress(app)

# SocketIO (используем evelent)
# socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Фильтр для шаблонов
@app.template_filter('dirname')
def dirname_filter(path):
    if not path:
        return ''
    return '/'.join(path.split('/')[:-1])

# Инициализация БД
db.init_app(app)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_server_or_404(server_id):
    server = db.session.get(Server, server_id)  # заменили Query.get
    if not server:
        abort(404)   # не return "Not found"
    if server.user_id == current_user.id or current_user in server.co_owners:
        return server
    abort(403)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Создание таблиц
with app.app_context():
    db.create_all()

# Запуск фонового обновления статусов (запускаем после создания таблиц)
# updater = StatusUpdater(app, interval=30)
# updater.start()

with app.app_context():
    db.create_all()
    db.session.execute(text("PRAGMA journal_mode=WAL"))
    db.session.commit()

# ---------- Роуты авторизации ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful, please login')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------- Основные роуты ----------

@app.route('/')
@login_required
def index():
    own_servers = Server.query.filter_by(user_id=current_user.id).all()
    co_servers = Server.query.join(server_access).filter(server_access.c.user_id == current_user.id).all()
    servers = list(set(own_servers + co_servers))

    # Обновляем статусы (без статистики, чтобы не нагружать)
    for server in servers:
        try:
            client = ssh_connect(
                host=server.ssh_host,
                port=server.ssh_port,
                user=server.ssh_user,
                password=server.get_password()
            )
            status = get_status(client, server.name)
            if server.status != status:
                server.status = status
            client.close()
        except Exception:
            server.status = 'offline'
    db.session.commit()

    return render_template('index.html', servers=servers)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_server(server):
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
            return redirect(url_for('add_server'))

        try:
            client = client = ssh_connect(
                    host=server.ssh_host,
                    port=server.ssh_port,
                    user=server.ssh_user,
                    password=server.get_password()
                )
            deploy_minecraft_server(client, name, server_type, version, password)
            client.close()

            server = Server(
                name=name,
                ssh_host=host,
                ssh_port=port,
                ssh_user=user,
                server_type=server_type,
                mc_version=version,
                user_id=current_user.id,
                status='running'
            )
            server.set_password(password)
            db.session.add(server)
            db.session.commit()
            # Инвалидируем кэш главной страницы
            cache.delete('index')
            flash('Server deployed successfully!')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error: {str(e)}')
            return redirect(url_for('add_server'))

    versions = {
        'vanilla': ['1.20.4', '1.19.4', '1.18.2'],
        'spigot': ['1.20.4', '1.19.4', '1.18.2'],
        'paper': ['1.20.4', '1.19.4', '1.18.2']
    }
    return render_template('add_server.html', versions=versions)

@app.route('/server/<int:server_id>')
@login_required
def server_detail(server_id):
    server = get_server_or_404(server_id)
    logs = ''
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
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
    server = get_server_or_404(server_id)  # <-- эта строка обязательна
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        stats = get_system_stats(client)
        client.close()
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            'cpu_percent': 0.0,
            'ram_total_mb': 0,
            'ram_used_mb': 0,
            'ram_percent': 0.0,
            'error': str(e)
        })

# Кэшированная функция для получения логов
@cache.memoize(timeout=5)
def get_logs_cached(server_id, server):
    client = ssh_connect(
        host=server.ssh_host,
        port=server.ssh_port,
        user=server.ssh_user,
        password=server.get_password()
    )
    logs = get_logs(client, server.name)
    client.close()
    return logs

@app.route('/server/<int:server_id>/start')
@login_required
def start_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        password = server.get_password()
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        start_server(client, server.name, password)
        client.close()
        server.status = 'running'
        db.session.commit()
        # Инвалидируем кэш главной
        cache.delete('index')
        flash('Server started')
    except Exception as e:
        flash(f'Error: {e}')
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/server/<int:server_id>/stop')
@login_required
def stop_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        stop_server(client, server.name)
        client.close()
        server.status = 'stopped'
        db.session.commit()
        cache.delete('index')
        flash('Server stopped')
    except Exception as e:
        flash(f'Error: {e}')
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/server/<int:server_id>/restart')
@login_required
def restart_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        password = server.get_password()
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        restart_server(client, server.name, password)
        client.close()
        server.status = 'running'
        db.session.commit()
        cache.delete('index')
        flash('Server restarted')
    except Exception as e:
        flash(f'Error restarting: {e}')
    return redirect(url_for('server_detail', server_id=server_id))

@app.route('/server/<int:server_id>/delete', methods=['POST'])
@login_required
def delete_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        delete_server(client, server.name)
        client.close()
        db.session.delete(server)
        db.session.commit()
        cache.delete('index')
        flash('Server deleted')
    except Exception as e:
        flash(f'Error: {e}')
    return redirect(url_for('index'))

# ---------- API для консоли (AJAX) ----------
@app.route('/server/<int:server_id>/api/command', methods=['POST'])
@login_required
def api_send_command(server_id):
    server = get_server_or_404(server_id)
    command = request.json.get('command')
    if not command:
        return jsonify({'status': 'error', 'message': 'No command'}), 400
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        send_command(client, server.name, command)
        client.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/server/<int:server_id>/api/logs')
@login_required
def api_get_logs(server_id):
    try:
        server = get_server_or_404(server_id)
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        logs = get_logs(client, server.name, lines=50)
        client.close()
        return jsonify({'logs': logs})
    except Exception as e:
        import traceback
        traceback.print_exc()  # печатаем стек в консоль
        return jsonify({'logs': f'Error: {str(e)}'}), 500

# ---------- Страница консоли (WebSocket) ----------
# @app.route('/server/<int:server_id>/console')
# @login_required
# def console(server_id):
#     server = get_server_or_404(server_id)
#     return render_template('console.html', server=server, active_page='console')

# ---------- WebSocket обработчики (оптимизированы) ----------
# tail_threads = {}
# ssh_clients = {}
# room_clients = {}  # количество клиентов в комнате
#
# def tail_logs_thread(server_id, server, client):
#     log_path = f"/home/{server.ssh_user}/minecraft_servers/{server.name}/logs/latest.log"
#     last_position = 0
#     batch = []
#     last_send_time = time.time()
#     while True:
#         try:
#             # Проверяем, есть ли активные клиенты в комнате
#             if server_id not in room_clients or room_clients[server_id] == 0:
#                 break
#             if not client.get_transport() or not client.get_transport().is_active():
#                 break
#             cmd = f"tail -n +{last_position+1} {log_path} 2>/dev/null"
#             out, err, code = execute_command(client, cmd, timeout=5)
#             if out:
#                 lines = out.splitlines()
#                 batch.extend(lines)
#                 last_position += len(lines)
#             if time.time() - last_send_time > 1 or len(batch) >= 10:
#                 if batch:
#                     socketio.emit('log_lines', {'lines': batch}, namespace='/console', room=str(server_id))
#                     batch = []
#                     last_send_time = time.time()
#             time.sleep(0.5)
#         except Exception as e:
#             socketio.emit('error', {'message': str(e)}, namespace='/console', room=str(server_id))
#             break
#     # Закрываем клиент при выходе
#     try:
#         client.close()
#     except:
#         pass
#     # Удаляем записи
#     if server_id in tail_threads:
#         del tail_threads[server_id]
#     if server_id in ssh_clients:
#         del ssh_clients[server_id]
#     if server_id in room_clients:
#         del room_clients[server_id]
#
# @socketio.on('connect', namespace='/console')
# def handle_console_connect():
#     print('Client connected to console namespace')
#
# @socketio.on('disconnect', namespace='/console')
# def handle_console_disconnect():
#     sid = request.sid
#     if sid in client_rooms:
#         server_id = client_rooms[sid]
#         if server_id in room_clients:
#             room_clients[server_id] -= 1
#             if room_clients[server_id] == 0:
#                 del room_clients[server_id]
#         del client_rooms[sid]
#
# @socketio.on('join', namespace='/console')
# def handle_console_join(data):
#     server_id = data.get('server_id')
#     if not server_id:
#         emit('error', {'message': 'No server_id provided'}, namespace='/console')
#         return
#     server = Server.query.get(server_id)
#     if not server:
#         emit('error', {'message': 'Server not found'}, namespace='/console')
#         return
#     if server.user_id != current_user.id and current_user not in server.co_owners:
#         emit('error', {'message': 'Access denied'}, namespace='/console')
#         return
#     # Запоминаем комнату для клиента
#     sid = request.sid
#     client_rooms[sid] = server_id
#
#     join_room(str(server_id))
#     emit('connected', {'message': f'Connected to {server.name}'}, namespace='/console')
#
#     if server_id not in room_clients:
#         room_clients[server_id] = 0
#     room_clients[server_id] += 1
#
#     if server_id not in tail_threads:
#         try:
#             client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
#             ssh_clients[server_id] = client
#             thread = threading.Thread(target=tail_logs_thread, args=(server_id, server, client))
#             thread.daemon = True
#             thread.start()
#             tail_threads[server_id] = thread
#         except Exception as e:
#             emit('error', {'message': str(e)}, namespace='/console')
#             room_clients[server_id] -= 1
#             if room_clients[server_id] == 0:
#                 del room_clients[server_id]
#             if server_id in client_rooms:
#                 del client_rooms[server_id]
#
# @socketio.on('send_command', namespace='/console')
# def handle_console_send_command(data):
#     server_id = data.get('server_id')
#     command = data.get('command')
#     if not server_id or not command:
#         emit('error', {'message': 'Invalid data'}, namespace='/console')
#         return
#     server = Server.query.get(server_id)
#     if not server:
#         emit('error', {'message': 'Server not found'}, namespace='/console')
#         return
#     if server.user_id != current_user.id and current_user not in server.co_owners:
#         emit('error', {'message': 'Access denied'}, namespace='/console')
#         return
#     client = ssh_clients.get(server_id)
#     if not client:
#         try:
#             client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
#             ssh_clients[server_id] = client
#         except Exception as e:
#             emit('error', {'message': str(e)}, namespace='/console')
#             return
#     try:
#         send_command(client, server.name, command)
#         emit('command_sent', {'command': command}, namespace='/console')
#     except Exception as e:
#         emit('error', {'message': str(e)}, namespace='/console')

# ---------- Разделы панели (Players, Files, Config, Plugins, Mods, Backups, Ports, Domain, Startup, Settings, Coowners, Change-core) ----------

@cache.memoize(timeout=5)
def get_logs_cached(server_id, server):
    client = ssh_connect(
        host=server.ssh_host,
        port=server.ssh_port,
        user=server.ssh_user,
        password=server.get_password()
    )
    logs = get_logs(client, server.name)
    client.close()
    return logs

@app.route('/server/<int:server_id>/players')
@login_required
def players(server_id):
    server = get_server_or_404(server_id)
    ops = []
    whitelist = []
    bans = []
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
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

@app.route('/server/<int:server_id>/files', methods=['GET', 'POST'])
@login_required
def files(server_id):
    server = get_server_or_404(server_id)
    path = request.args.get('path', '')
    if request.method == 'POST':
        if 'file' in request.files:
            f = request.files['file']
            if f.filename:
                content = f.read().decode('utf-8')
                try:
                    client = ssh_connect(
                        host=server.ssh_host,
                        port=server.ssh_port,
                        user=server.ssh_user,
                        password=server.get_password()
                    )
                    write_file_content(client, server.name, path + '/' + f.filename if path else f.filename, content)
                    client.close()
                    flash('Файл загружен')
                except Exception as e:
                    flash(f'Ошибка: {e}')
        if 'new_dir' in request.form:
            dirname = request.form['new_dir']
            try:
                client = ssh_connect(
                    host=server.ssh_host,
                    port=server.ssh_port,
                    user=server.ssh_user,
                    password=server.get_password()
                )
                create_directory(client, server.name, path + '/' + dirname if path else dirname)
                client.close()
                flash('Директория создана')
            except Exception as e:
                flash(f'Ошибка: {e}')
        return redirect(url_for('files', server_id=server.id, path=path))
    file_list = []
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
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
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        content = get_file_content(client, server.name, file_path)
        client.close()
        if content is None:
            flash('Файл не найден')
            return redirect(url_for('files', server_id=server.id))
        return Response(content, mimetype='application/octet-stream', headers={"Content-Disposition": f"attachment;filename={file_path.split('/')[-1]}"})
    except Exception as e:
        flash(f'Ошибка: {e}')
        return redirect(url_for('files', server_id=server.id))

@app.route('/server/<int:server_id>/files/delete', methods=['POST'])
@login_required
def delete_file(server_id):
    server = get_server_or_404(server_id)
    file_path = request.args.get('file')
    if not file_path:
        abort(400)
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        delete_file(client, server.name, file_path)
        client.close()
        return '', 200
    except Exception as e:
        return str(e), 500

@app.route('/server/<int:server_id>/config', methods=['GET', 'POST'])
@login_required
def config(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        try:
            client = ssh_connect(
                host=server.ssh_host,
                port=server.ssh_port,
                user=server.ssh_user,
                password=server.get_password()
            )
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
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
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
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
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
                client = ssh_connect(
                    host=server.ssh_host,
                    port=server.ssh_port,
                    user=server.ssh_user,
                    password=server.get_password()
                )
                install_plugin(client, server.name, plugin_url, plugin_name)
                client.close()
                flash('Плагин установлен')
            except Exception as e:
                flash(f'Ошибка: {e}')
        return redirect(url_for('plugins', server_id=server.id))
    return render_template('plugins.html', server=server, installed_plugins=installed_plugins, active_page='plugins')

@app.route('/server/<int:server_id>/mods')
@login_required
def mods(server_id):
    server = get_server_or_404(server_id)
    installed_mods = []
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
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

@app.route('/server/<int:server_id>/backups', methods=['GET', 'POST'])
@login_required
def backups(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        if 'create' in request.form:
            try:
                client = ssh_connect(
                    host=server.ssh_host,
                    port=server.ssh_port,
                    user=server.ssh_user,
                    password=server.get_password()
                )
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
                    client = ssh_connect(
                        host=server.ssh_host,
                        port=server.ssh_port,
                        user=server.ssh_user,
                        password=server.get_password()
                    )
                    restore_backup(client, server.name, backup_name)
                    client.close()
                    flash('Бэкап восстановлен')
                except Exception as e:
                    flash(f'Ошибка: {e}')
        return redirect(url_for('backups', server_id=server.id))
    backups_list = []
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
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
    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        props = read_server_properties(client, server.name)
        port = int(props.get('server-port', 25565))
        client.close()
    except:
        pass
    if request.method == 'POST':
        new_port = request.form.get('port')
        if new_port:
            try:
                client = ssh_connect(
                    host=server.ssh_host,
                    port=server.ssh_port,
                    user=server.ssh_user,
                    password=server.get_password()
                )
                props = read_server_properties(client, server.name)
                props['server-port'] = new_port
                write_server_properties(client, server.name, props)
                client.close()
                flash('Порт обновлён (требуется перезапуск сервера)')
            except Exception as e:
                flash(f'Ошибка: {e}')
        return redirect(url_for('ports', server_id=server.id))
    return render_template('ports.html', server=server, port=port, active_page='ports')

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
        server.memory_percent = int(request.form.get('memory_percent', server.memory_percent))
        server.timezone = request.form.get('timezone', server.timezone)
        server.garbage_collector = request.form.get('garbage_collector', server.garbage_collector)
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
    coowners_list = server.co_owners.all()  # получаем объекты User
    return render_template('coowners.html', server=server, coowners=coowners_list, active_page='coowners')

@app.route('/server/<int:server_id>/change-core', methods=['GET', 'POST'])
@login_required
def change_core(server_id):
    server = get_server_or_404(server_id)
    if request.method == 'POST':
        new_type = request.form.get('server_type')
        new_version = request.form.get('mc_version')
        if new_type and new_version:
            try:
                client = ssh_connect(
                    host=server.ssh_host,
                    port=server.ssh_port,
                    user=server.ssh_user,
                    password=server.get_password()
                )
                stop_server(client, server.name)
                execute_command(client, f"rm -f ~/minecraft_servers/{server.name}/server.jar")
                jar_url = get_jar_url(new_type, new_version)
                if not jar_url:
                    flash('Не найден URL для указанного ядра и версии')
                    return redirect(url_for('change_core', server_id=server.id))
                execute_command(client, f"wget -O ~/minecraft_servers/{server.name}/server.jar {jar_url}")
                server.server_type = new_type
                server.mc_version = new_version
                db.session.commit()
                flash(f'Ядро изменено на {new_type} {new_version}. Запустите сервер.')
                client.close()
            except Exception as e:
                flash(f'Ошибка: {e}')
        return redirect(url_for('change_core', server_id=server.id))
    versions = {
        'vanilla': ['1.20.4', '1.19.4', '1.18.2'],
        'spigot': ['1.20.4', '1.19.4', '1.18.2'],
        'paper': ['1.20.4', '1.19.4', '1.18.2']
    }
    return render_template('change_core.html', server=server, versions=versions, active_page='change_core')

#Моды и плагины

@app.route('/api/modrinth/install/<int:server_id>', methods=['POST'])
@login_required
def modrinth_install(server_id):
    """Устанавливает мод/плагин на сервер."""
    server = get_server_or_404(server_id)
    data = request.get_json()
    project_id = data.get('project_id')
    version_id = data.get('version_id')
    project_type = data.get('type')  # 'mod' или 'plugin'

    if not project_id or not version_id or not project_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        client = ssh_connect(
            host=server.ssh_host,
            port=server.ssh_port,
            user=server.ssh_user,
            password=server.get_password()
        )
        filename = install_modrinth_project(client, server.name, project_id, version_id, project_type)
        client.close()
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/modrinth/search')
@login_required
def modrinth_search():
    query = request.args.get('query', '')
    project_type = request.args.get('type', 'mod')  # 'mod' или 'plugin'
    version = request.args.get('version', '')  # версия Minecraft, например '1.20.4'
    loader = request.args.get('loader', '')  # для модов: fabric, neoforge, forge, quilt
    limit = int(request.args.get('limit', 20))
    if not query:
        return jsonify({'projects': []})

    facets = [[f'project_type:{project_type}']]
    if version:
        facets.append([f'versions:{version}'])
    if loader and project_type == 'mod':
        facets.append([f'categories:{loader}'])  # или facets: [['categories:fabric']]
    # Формируем запрос
    url = "https://api.modrinth.com/v2/search"
    params = {
        'query': query,
        'limit': limit,
        'facets': json.dumps(facets)
    }
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
        versions = resp.json()
        result = []
        for v in versions:
            # Фильтруем по версии Minecraft и загрузчику, если указаны
            game_versions = v.get('game_versions', [])
            if version_filter and version_filter not in game_versions:
                continue
            if loader_filter:
                # Проверяем, есть ли загрузчик в списке loaders
                loaders = v.get('loaders', [])
                if loader_filter not in loaders:
                    continue
            result.append({
                'id': v['id'],
                'version_number': v.get('version_number', ''),
                'game_versions': v.get('game_versions', []),
                'release_channel': v.get('release_channel', ''),
                'loaders': v.get('loaders', []),
                'files': v.get('files', [])
            })
        return jsonify({'versions': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/server/<int:server_id>/console')
@login_required
def console(server_id):
    server = get_server_or_404(server_id)
    return render_template('console.html', server=server, active_page='console')

# ---------- Запуск ----------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)