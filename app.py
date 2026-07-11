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

# -----------------------------------------------
# Список версий для разных типов ядер
# (оставлен как в вашем коде)
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

# ------------------------------------------------------------
# Инициализация приложения
# ------------------------------------------------------------
app = Flask(__name__)
app.config.from_object(Config)

# Кэш и сжатие
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})
compress = Compress(app)

# SocketIO (без WebSocket для лёгкости, можно оставить для будущего)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Фильтр для шаблонов
@app.template_filter('dirname')
def dirname_filter(path):
    if not path:
        return ''
    return '/'.join(path.split('/')[:-1])

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
    db.session.commit()

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

# ------------------------------------------------------------
# Основные страницы
# ------------------------------------------------------------
@app.route('/')
@login_required
def index():
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
            return redirect(url_for('add_server'))

        try:
            client = ssh_connect(host, port, user, password)
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
            cache.delete('index')
            flash('Server deployed successfully!')
            return redirect(url_for('index'))
        except Exception as e:
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

@cache.memoize(timeout=5)
def get_logs_cached(server_id, server):
    client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
    logs = get_logs(client, server.name)
    client.close()
    return logs

@app.route('/server/<int:server_id>/api/logs')
@login_required
def api_get_logs(server_id):
    try:
        server = get_server_or_404(server_id)
        logs = get_logs_cached(server_id, server)
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'logs': f'Error: {str(e)}'}), 500

# ------------------------------------------------------------
# Управление сервером (start, stop, restart, delete)
# ------------------------------------------------------------
@app.route('/server/<int:server_id>/start')
@login_required
def start_server_route(server_id):
    server = get_server_or_404(server_id)
    try:
        password = server.get_password()
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, password)
        start_server_via_nohup(client, server.name, password, server.java_path if hasattr(server, 'java_path') else "java")
        client.close()
        server.status = 'running'
        db.session.commit()
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
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
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
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, password)
        restart_server(client, server.name, password, server.java_path if hasattr(server, 'java_path') else "java")
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
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        delete_server(client, server.name)
        client.close()
        db.session.delete(server)
        db.session.commit()
        cache.delete('index')
        flash('Server deleted')
    except Exception as e:
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
            write_file_content(client, server.name, file_path, content)
            client.close()
            flash('Файл сохранён')
        except Exception as e:
            flash(f'Ошибка сохранения: {e}')
        return redirect(url_for('files', server_id=server.id, path='/'.join(file_path.split('/')[:-1]) if '/' in file_path else ''))

    # GET: читаем содержимое файла
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
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
def delete_file(server_id):
    server = get_server_or_404(server_id)
    file_path = request.args.get('file')
    if not file_path:
        abort(400)
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        delete_file_or_directory(client, server.name, file_path)
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
                content = f.read().decode('utf-8')
                try:
                    client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                    write_file_content(client, server.name, path + '/' + f.filename if path else f.filename, content)
                    client.close()
                    flash('Файл загружен')
                except Exception as e:
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

@app.route('/server/<int:server_id>/files/delete', methods=['POST'])
@login_required
def delete_server_file(server_id):
    # ... код
    server = get_server_or_404(server_id)
    file_path = request.args.get('file')
    if not file_path:
        abort(400)
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
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
        if new_type and new_version:
            try:
                client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
                stop_server(client, server.name)
                execute_command(client, f"rm -f ~/minecraft_servers/{server.name}/server.jar")
                jar_url = get_jar_url(new_type, new_version)
                if not jar_url:
                    flash('Не найден URL для указанного ядра и версии')
                    return redirect(url_for('change_core', server_id=server.id))
                execute_command(client, f"curl -L -o ~/minecraft_servers/{server.name}/server.jar {jar_url}")
                rename_jar_to_server(client, f"/home/{server.ssh_user}/minecraft_servers/{server.name}")
                server.server_type = new_type
                server.mc_version = new_version
                db.session.commit()
                flash(f'Ядро изменено на {new_type} {new_version}. Запустите сервер.')
                client.close()
            except Exception as e:
                flash(f'Ошибка: {e}')
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
    if not project_id or not version_id or not project_type:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        client = ssh_connect(server.ssh_host, server.ssh_port, server.ssh_user, server.get_password())
        filename = install_modrinth_project(client, server.name, project_id, version_id, project_type)
        client.close()
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ------------------------------------------------------------
# Запуск
# ------------------------------------------------------------
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)