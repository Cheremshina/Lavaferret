import paramiko
import time
import os
import tempfile
import requests
import json
import re

# Конфигурация JAR-ссылок (можно расширить)
JAR_URLS = {
    'vanilla': {
        '1.20.4': 'https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.ja',
        '1.19.4': 'https://piston-data.mojang.com/v1/objects/...',
        '1.18.2': 'https://piston-data.mojang.com/v1/objects/...'
    },
    'spigot': {
        '1.20.4': 'https://download.getbukkit.org/spigot/spigot-1.20.4.jar',
        '1.19.4': 'https://download.getbukkit.org/spigot/spigot-1.19.4.jar',
        '1.18.2': 'https://download.getbukkit.org/spigot/spigot-1.18.2.jar'
    },
    'paper': {
        '1.20.4': 'https://api.papermc.io/v2/projects/paper/versions/1.20.4/builds/.../downloads/paper-1.20.4-...jar',
        '1.19.4': 'https://api.papermc.io/v2/projects/paper/versions/1.19.4/builds/.../downloads/paper-1.19.4-...jar',
        '1.18.2': 'https://api.papermc.io/v2/projects/paper/versions/1.18.2/builds/.../downloads/paper-1.18.2-...jar'
    }
}

def get_jar_url(server_type, version):
    if server_type == 'vanilla':
        vanilla_urls = {
            '1.20.4': 'https://piston-data.mojang.com/v1/objects/8dd1a28015f51b1803213892b50b7b4fc76e594d/server.jar',
            '1.19.4': 'https://piston-data.mojang.com/v1/objects/8f3112a1049751cc472ec13e397eade5336ca7ae/server.jar',
            '1.18.2': 'https://piston-data.mojang.com/v1/objects/c8f83c5655308435b3dcf03c06d9fe8740a77469/server.jar',
        }
        return vanilla_urls.get(version, '')
    elif server_type == 'spigot':
        spigot_urls = {
            '1.20.4': 'https://download.getbukkit.org/spigot/spigot-1.20.4.jar',
            '1.19.4': 'https://download.getbukkit.org/spigot/spigot-1.19.4.jar',
            '1.18.2': 'https://download.getbukkit.org/spigot/spigot-1.18.2.jar',
        }
        return spigot_urls.get(version, '')
    elif server_type == 'paper':
        try:
            api_url = f'https://api.papermc.io/v2/projects/paper/versions/{version}'
            resp = requests.get(api_url)
            resp.raise_for_status()
            builds = resp.json()['builds']
            if builds:
                latest = builds[-1]
                return f'https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{latest}/downloads/paper-{version}-{latest}.jar'
        except:
            pass
        return ''
    else:
        return ''

def install_modrinth_project(client, server_name, project_id, version_id, project_type):
    """
    Устанавливает мод или плагин с Modrinth.
    project_type: 'mod' или 'plugin'
    """
    if project_type not in ['mod', 'plugin']:
        raise ValueError("project_type must be 'mod' or 'plugin'")

    # Определяем папку
    base_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}"
    if project_type == 'mod':
        target_dir = f"{base_dir}/mods"
    else:
        target_dir = f"{base_dir}/plugins"

    # Создаём папку, если её нет
    execute_command(client, f"mkdir -p {target_dir}")

    # Получаем URL для скачивания через API Modrinth
    # Используем версию, если передан version_id, иначе берём последнюю
    if version_id:
        version_url = f"https://api.modrinth.com/v2/version/{version_id}"
    else:
        # Если version_id не передан, получаем последнюю версию проекта
        # Но мы будем передавать version_id из интерфейса
        raise Exception("version_id is required")

    # Запрашиваем информацию о версии
    import requests
    resp = requests.get(version_url)
    if resp.status_code != 200:
        raise Exception(f"Failed to get version info: {resp.text}")
    version_data = resp.json()
    # Находим первый файл (обычно jar)
    files = version_data.get('files', [])
    if not files:
        raise Exception("No files found for this version")
    # Берём первый файл (можно также искать по primary)
    file_info = files[0]
    download_url = file_info.get('url')
    filename = file_info.get('filename')
    if not download_url or not filename:
        raise Exception("Download URL or filename missing")

    # Скачиваем файл на удалённый сервер
    cmd = f"curl -L -o {target_dir}/{filename} {download_url}"
    out, err, code = execute_command(client, cmd, timeout=60)
    if code != 0:
        raise Exception(f"Download failed: {err}\n{out}")
    return filename

def ssh_connect(host, port, user, password):
    # Проверка на пустые значения
    if not all([host, port, user, password]):
        raise ValueError("All arguments (host, port, user, password) are required")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=port,
            username=user,
            password=password,
            timeout=30,
            allow_agent=False,
            look_for_keys=False
        )
        transport = client.get_transport()
        if transport:
            transport.set_keepalive(30)
        return client
    except Exception as e:
        raise Exception(f"SSH connection failed: {str(e)}")

def execute_command(client, command, sudo=False, timeout=30, retries=2):
    if sudo:
        command = f"sudo {command}"
    for attempt in range(retries + 1):
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            output = stdout.read().decode()
            error = stderr.read().decode()
            return output, error, exit_status
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
                try:
                    if not client.get_transport() or not client.get_transport().is_active():
                        raise Exception("Transport inactive")
                except:
                    pass
                continue
            raise Exception(f"Command execution failed: {str(e)}")
    return "", "", -1

def ensure_java_installed(client, password=None):
    out, err, code = execute_command(client, "java -version 2>&1 | head -n1 | grep -o 'version'")
    if code == 0:
        return True
    out, err, code = execute_command(client, "cat /etc/os-release | grep -E '^ID=' | cut -d= -f2")
    os_id = out.strip().lower().strip('"')
    if 'ubuntu' in os_id or 'debian' in os_id:
        install_cmd = "apt update && apt install -y openjdk-17-jre-headless -y"
    elif 'centos' in os_id or 'rhel' in os_id or 'fedora' in os_id:
        install_cmd = "yum install -y java-17-openjdk-headless -y || dnf install -y java-17-openjdk-headless -y"
    else:
        raise Exception("Unsupported OS for auto Java installation")
    if password:
        escaped_password = password.replace("'", "'\\''")
        full_cmd = f"echo '{escaped_password}' | sudo -S bash -c '{install_cmd}'"
    else:
        full_cmd = f"sudo bash -c '{install_cmd}'"
    out, err, code = execute_command(client, full_cmd)
    if code != 0:
        raise Exception(f"Failed to install Java: {err}")
    return True

def is_server_running(client, server_name):
    # Проверка по процессу Java
    cmd_ps = f"ps aux | grep -v grep | grep 'java.*server.jar' | grep '/home/[^/]*/minecraft_servers/{server_name}' | wc -l"
    try:
        out, err, code = execute_command(client, cmd_ps, timeout=5)
        if code == 0 and int(out.strip()) > 0:
            return True
    except:
        pass
    # Проверка screen
    try:
        out, err, code = execute_command(client, f"screen -ls | grep 'mc-{server_name}'", timeout=5)
        if code == 0 and out.strip():
            return True
    except:
        pass
    return False

def get_status(client, server_name):
    if is_server_running(client, server_name):
        return 'running'
    else:
        # Проверка существования папки
        cmd_dir = f"test -d /home/{client._transport.get_username()}/minecraft_servers/{server_name}"
        _, _, code_dir = execute_command(client, cmd_dir, timeout=5)
        if code_dir == 0:
            return 'stopped'
        else:
            return 'not_deployed'

def get_logs(client, server_name, lines=50):
    username = client._transport.get_username()
    log_path = f"/home/{username}/minecraft_servers/{server_name}/logs/latest.log"
    cmd = f"tail -n {lines} {log_path} 2>/dev/null || echo 'Log file not found'"
    out, err, code = execute_command(client, cmd, timeout=10)
    return out

def wait_for_server(client, server_name, timeout=40):
    """
    Ожидает запуска сервера, проверяя статус каждые 2 секунды.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_server_running(client, server_name):
            # Дополнительно проверяем логи на готовность
            logs = get_logs(client, server_name, lines=3)
            if "Done" in logs or "For help, type" in logs:
                return True
        time.sleep(2)
    return False

def ensure_screen_installed(client, password=None):
    """Проверяет наличие screen и устанавливает, если отсутствует."""
    out, err, code = execute_command(client, "which screen", timeout=5)
    if code == 0:
        return True
    # Определяем ОС
    out, err, code = execute_command(client, "cat /etc/os-release | grep -E '^ID=' | cut -d= -f2")
    os_id = out.strip().lower().strip('"')
    if 'ubuntu' in os_id or 'debian' in os_id:
        install_cmd = "apt update && apt install -y screen"
    elif 'centos' in os_id or 'rhel' in os_id or 'fedora' in os_id:
        install_cmd = "yum install -y screen || dnf install -y screen"
    else:
        raise Exception("Unsupported OS for auto screen installation")
    if password:
        escaped_password = password.replace("'", "'\\''")
        full_cmd = f"echo '{escaped_password}' | sudo -S bash -c '{install_cmd}'"
    else:
        full_cmd = f"sudo bash -c '{install_cmd}'"
    out, err, code = execute_command(client, full_cmd, timeout=60)
    if code != 0:
        raise Exception(f"Failed to install screen: {err}")
    return True

def get_free_port(client, base_port=25565, max_attempts=10):
    """Находит первый свободный порт, начиная с base_port."""
    for port in range(base_port, base_port + max_attempts):
        check_cmd = f"ss -tlnp | grep ':{port} ' || netstat -tlnp 2>/dev/null | grep ':{port} '"
        out, _, code = execute_command(client, check_cmd, timeout=5)
        if code != 0 and not out.strip():
            return port
    raise Exception("No free port found")

def deploy_minecraft_server(client, server_name, server_type, mc_version, password):
    ensure_java_installed(client, password)
    ensure_screen_installed(client, password)
    username = client._transport.get_username()
    base_dir = f"/home/{username}/minecraft_servers"
    server_dir = f"{base_dir}/{server_name}"
    execute_command(client, f"mkdir -p {server_dir}")

    jar_url = get_jar_url(server_type, mc_version)
    if not jar_url:
        raise Exception(f"No JAR URL found for {server_type} {mc_version}")

    cmd_download = f"curl -L -o {server_dir}/server.jar {jar_url}"
    out, err, code = execute_command(client, cmd_download, timeout=60)
    if code != 0:
        raise Exception(f"Download failed: {err}\n{out}")

    # Проверка JAR
    check_cmd = f"file {server_dir}/server.jar | grep -q 'Zip archive'"
    _, _, check_code = execute_command(client, check_cmd, timeout=5)
    if check_code != 0:
        head_cmd = f"head -c 200 {server_dir}/server.jar"
        head_out, _, _ = execute_command(client, head_cmd, timeout=5)
        raise Exception(f"Downloaded file is not a JAR (probably HTML). First 200 chars: {head_out}")

    # eula.txt
    execute_command(client, f"echo 'eula=true' > {server_dir}/eula.txt")

    # Находим свободный порт
    server_port = get_free_port(client, 25565)
    properties_content = f"""#Minecraft server properties
enable-jmx-monitoring=false
rcon.port=25575
level-seed=
gamemode=survival
enable-command-block=false
enable-query=false
generator-settings=
enforce-secure-profile=true
level-name=world
motd=A Minecraft Server
query.port=25565
pvp=true
generate-structures=true
max-chained-neighbor-updates=1000000
difficulty=easy
network-compression-threshold=256
max-tick-time=60000
require-resource-pack=false
use-native-transport=true
max-players=20
online-mode=true
enable-status=true
allow-flight=false
initial-enabled-packs=vanilla
broadcast-rcon-to-ops=true
view-distance=10
server-ip=
resource-pack-prompt=
allow-nether=true
server-port={server_port}
enable-rcon=false
sync-chunk-writes=true
op-permission-level=4
prevent-proxy-connections=false
resource-pack=
hide-online-players=false
entity-broadcast-range-percentage=100
simulation-distance=10
rcon.password=
player-idle-timeout=0
debug=false
force-gamemode=false
rate-limit=0
hardcore=false
white-list=false
broadcast-console-to-ops=true
spawn-npcs=true
spawn-animals=true
snooper-enabled=false
function-permission-level=2
text-filtering-config=
spawn-monsters=true
enforce-whitelist=false
resource-pack-sha1=
spawn-protection=16
max-world-size=29999984
"""
    with tempfile.NamedTemporaryFile(mode='w', newline='\n', delete=False, suffix='.tmp') as tmp:
        tmp.write(properties_content)
        tmp_path = tmp.name
    try:
        sftp = client.open_sftp()
        sftp.put(tmp_path, f"{server_dir}/server.properties")
        sftp.close()
    finally:
        os.remove(tmp_path)

    # start.sh
    start_script = f"""#!/bin/bash
cd {server_dir}
java -Xmx1024M -Xms1024M -jar server.jar nogui
"""
    with tempfile.NamedTemporaryFile(mode='w', newline='\n', delete=False, suffix='.sh') as tmp:
        tmp.write(start_script)
        tmp_path = tmp.name
    try:
        sftp = client.open_sftp()
        sftp.put(tmp_path, f"{server_dir}/start.sh")
        sftp.close()
    finally:
        os.remove(tmp_path)

    execute_command(client, f"chmod +x {server_dir}/start.sh")
    cmd = f"screen -dmS mc-{server_name} bash {server_dir}/start.sh"
    out, err, code = execute_command(client, cmd, timeout=10)
    if code != 0:
        raise Exception(f"Screen start failed: {err}\n{out}")

    time.sleep(2)
    screen_check, _, _ = execute_command(client, f"screen -ls | grep 'mc-{server_name}'", timeout=5)
    if not screen_check.strip():
        raise Exception("Screen session not created")

    if not wait_for_server(client, server_name, timeout=60):
        logs = get_logs(client, server_name, lines=30)
        raise Exception(f"Server failed to start within timeout, latest logs:\n{logs}")
    return True

def start_server(client, server_name, password):
    ensure_screen_installed(client, password)
    if is_server_running(client, server_name):
        return True
    username = client._transport.get_username()
    server_dir = f"/home/{username}/minecraft_servers/{server_name}"
    # Проверяем и при необходимости меняем порт
    props = read_server_properties(client, server_name)
    if props:
        current_port = int(props.get('server-port', 25565))
        # Проверяем, занят ли порт
        check_cmd = f"ss -tlnp | grep ':{current_port} ' || netstat -tlnp 2>/dev/null | grep ':{current_port} '"
        out, _, code = execute_command(client, check_cmd, timeout=5)
        if code == 0 and out.strip():
            # Порт занят, ищем новый
            new_port = get_free_port(client, 25565)
            props['server-port'] = str(new_port)
            write_server_properties(client, server_name, props)

    # Убедимся, что start.sh существует
    check_script = f"test -f {server_dir}/start.sh"
    _, _, code = execute_command(client, check_script, timeout=5)
    if code != 0:
        start_script = f"""#!/bin/bash
cd {server_dir}
java -Xmx1024M -Xms1024M -jar server.jar nogui
"""
        with tempfile.NamedTemporaryFile(mode='w', newline='\n', delete=False, suffix='.sh') as tmp:
            tmp.write(start_script)
            tmp_path = tmp.name
        try:
            sftp = client.open_sftp()
            sftp.put(tmp_path, f"{server_dir}/start.sh")
            sftp.close()
        finally:
            os.remove(tmp_path)
        execute_command(client, f"chmod +x {server_dir}/start.sh")

    cmd = f"screen -dmS mc-{server_name} bash {server_dir}/start.sh"
    out, err, code = execute_command(client, cmd, timeout=10)
    if code != 0:
        return False
    time.sleep(2)
    screen_check, _, _ = execute_command(client, f"screen -ls | grep 'mc-{server_name}'", timeout=5)
    if not screen_check.strip():
        return False
    return wait_for_server(client, server_name, timeout=60)

def stop_server(client, server_name):
    # Пытаемся отправить stop через screen, если есть
    try:
        cmd_stop = f"screen -S mc-{server_name} -p 0 -X stuff 'stop\\015'"
        execute_command(client, cmd_stop, timeout=5)
        time.sleep(3)
    except:
        pass
    # Принудительно убиваем процесс Java
    execute_command(client, f"pkill -f 'java.*{server_name}.*server.jar'", timeout=5)
    # Убиваем screen сессию, если есть
    execute_command(client, f"screen -S mc-{server_name} -X quit", timeout=5)
    return True

def restart_server(client, server_name, password):
    stop_server(client, server_name)
    time.sleep(2)
    return start_server(client, server_name, password)

def send_command(client, server_name, command):
    # Проверяем, существует ли screen-сессия
    check = execute_command(client, f"screen -ls | grep 'mc-{server_name}'", timeout=5)
    if not check[0].strip():
        raise Exception("Screen session not found. Server is offline or not started via screen.")
    cmd = f"screen -S mc-{server_name} -p 0 -X stuff '{command}\\015'"
    out, err, code = execute_command(client, cmd, timeout=5)
    if code != 0:
        raise Exception(f"Failed to send command: {err}")
    return True

def delete_server(client, server_name):
    stop_server(client, server_name)
    execute_command(client, f"rm -rf ~/minecraft_servers/{server_name}")
    return True

def start_server_via_screen(client, server_name, server_dir):
    # Создаём start.sh с LF-окончаниями
    script_content = f"""#!/bin/bash
cd {server_dir}
java -Xmx1024M -Xms1024M -jar server.jar nogui
"""
    # Записываем через SFTP с newline='\n'
    with tempfile.NamedTemporaryFile(mode='w', newline='\n', delete=False, suffix='.sh') as tmp:
        tmp.write(script_content)
        tmp_path = tmp.name
    try:
        sftp = client.open_sftp()
        sftp.put(tmp_path, f"{server_dir}/start.sh")
        sftp.close()
    finally:
        os.remove(tmp_path)
    execute_command(client, f"chmod +x {server_dir}/start.sh")
    cmd = f"screen -dmS mc-{server_name} bash {server_dir}/start.sh"
    out, err, code = execute_command(client, cmd, timeout=10)
    if code != 0:
        raise Exception(f"Screen start failed: {err}\n{out}")
    return True

def get_system_stats(client):
    """
    Получает статистику системы через SSH:
    - загрузка CPU (%)
    - общая память (МБ), используемая память (МБ), процент использования
    Возвращает словарь.
    """
    stats = {}
    try:
        # CPU: берём idle и вычисляем usage = 100 - idle
        # Используем top -bn1, берём строку с Cpu(s)
        out, err, code = execute_command(client, "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1", timeout=5)
        if code == 0 and out.strip():
            # В некоторых версиях top выводит "us" (user) - лучше взять idle
            # Попробуем другой способ: через mpstat, если доступен
            out2, err2, code2 = execute_command(client, "mpstat 1 1 | tail -n1 | awk '{print 100 - $NF}'", timeout=5)
            if code2 == 0 and out2.strip():
                cpu_usage = float(out2.strip())
            else:
                # Запасной вариант: берём idle из top
                # top -bn1 | grep "Cpu(s)" | awk '{print $8}' - это idle (в некоторых версиях)
                out_idle, err_idle, code_idle = execute_command(client, "top -bn1 | grep 'Cpu(s)' | awk '{print $8}' | cut -d'%' -f1", timeout=5)
                if code_idle == 0 and out_idle.strip():
                    idle = float(out_idle.strip())
                    cpu_usage = 100 - idle
                else:
                    # Ещё вариант: читаем /proc/stat
                    out_stat, err_stat, code_stat = execute_command(client, "cat /proc/stat | grep '^cpu ' | awk '{print ($2+$4)*100/($2+$4+$5)}'", timeout=5)
                    if code_stat == 0 and out_stat.strip():
                        cpu_usage = float(out_stat.strip())
                    else:
                        cpu_usage = 0.0
        else:
            cpu_usage = 0.0
        stats['cpu_percent'] = round(cpu_usage, 1)

        # RAM: используем free -m
        out_ram, err_ram, code_ram = execute_command(client, "free -m | grep Mem | awk '{print $2, $3, $7}'", timeout=5)
        if code_ram == 0 and out_ram.strip():
            parts = out_ram.strip().split()
            if len(parts) >= 3:
                total_mb = int(parts[0])
                used_mb = int(parts[1])
                # parts[2] - available (может быть)
                stats['ram_total_mb'] = total_mb
                stats['ram_used_mb'] = used_mb
                stats['ram_percent'] = round((used_mb / total_mb) * 100, 1) if total_mb > 0 else 0.0
            else:
                stats['ram_total_mb'] = 0
                stats['ram_used_mb'] = 0
                stats['ram_percent'] = 0.0
        else:
            stats['ram_total_mb'] = 0
            stats['ram_used_mb'] = 0
            stats['ram_percent'] = 0.0
    except Exception as e:
        # В случае ошибки возвращаем нулевые значения
        stats = {
            'cpu_percent': 0.0,
            'ram_total_mb': 0,
            'ram_used_mb': 0,
            'ram_percent': 0.0
        }
    return stats

# ----- Управление файлами и конфигом -----
def list_files(client, server_name, path=''):
    full_path = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{path}"
    out, err, code = execute_command(client, f"ls -la {full_path}")
    files = []
    if code == 0:
        lines = out.strip().split('\n')
        for line in lines:
            if not line or line.startswith('total'):
                continue
            parts = line.split(maxsplit=8)
            if len(parts) >= 9:
                files.append({
                    'perms': parts[0],
                    'links': parts[1],
                    'user': parts[2],
                    'group': parts[3],
                    'size': parts[4],
                    'date': parts[5]+' '+parts[6]+' '+parts[7],
                    'name': parts[8]
                })
    return files

def get_file_content(client, server_name, file_path):
    full_path = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{file_path}"
    out, err, code = execute_command(client, f"cat {full_path}")
    if code == 0:
        return out
    return None

def write_file_content(client, server_name, file_path, content):
    full_path = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{file_path}"
    # Записываем с LF, чтобы избежать проблем с CRLF
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tmp', newline='\n') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        sftp = client.open_sftp()
        sftp.put(tmp_path, full_path)
        sftp.close()
    finally:
        os.remove(tmp_path)
    return True

def delete_file(client, server_name, file_path):
    full_path = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{file_path}"
    execute_command(client, f"rm -rf {full_path}")
    return True

def create_directory(client, server_name, dir_path):
    full_path = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/{dir_path}"
    execute_command(client, f"mkdir -p {full_path}")
    return True

def read_server_properties(client, server_name):
    content = get_file_content(client, server_name, 'server.properties')
    if not content:
        return {}
    props = {}
    for line in content.split('\n'):
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            props[k.strip()] = v.strip()
    return props

def write_server_properties(client, server_name, props):
    content = ""
    for k, v in props.items():
        content += f"{k}={v}\n"
    write_file_content(client, server_name, 'server.properties', content)
    return True

def create_backup(client, server_name):
    server_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}"
    backup_dir = f"{server_dir}/backups"
    execute_command(client, f"mkdir -p {backup_dir}")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.zip"
    cmd = f"cd {server_dir} && zip -r {backup_file} . -x 'backups/*'"
    out, err, code = execute_command(client, cmd)
    if code == 0:
        return backup_file
    return None

def list_backups(client, server_name):
    server_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/backups"
    out, err, code = execute_command(client, f"ls -la {server_dir}")
    backups = []
    if code == 0:
        lines = out.strip().split('\n')
        for line in lines:
            if not line or line.startswith('total'):
                continue
            parts = line.split(maxsplit=8)
            if len(parts) >= 9 and parts[8].endswith('.zip'):
                backups.append({
                    'name': parts[8],
                    'size': parts[4],
                    'date': parts[5]+' '+parts[6]+' '+parts[7]
                })
    return backups

def restore_backup(client, server_name, backup_name):
    server_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}"
    backup_path = f"{server_dir}/backups/{backup_name}"
    stop_server(client, server_name)
    execute_command(client, f"find {server_dir} -mindepth 1 -maxdepth 1 ! -name 'backups' -exec rm -rf {{}} +")
    execute_command(client, f"unzip -o {backup_path} -d {server_dir}")
    start_server(client, server_name, None)  # пароль не нужен для запуска, если Java уже есть
    return True

def install_plugin(client, server_name, plugin_url, plugin_name):
    plugins_dir = f"/home/{client._transport.get_username()}/minecraft_servers/{server_name}/plugins"
    execute_command(client, f"mkdir -p {plugins_dir}")
    cmd = f"wget -O {plugins_dir}/{plugin_name} {plugin_url}"
    execute_command(client, cmd)
    return True