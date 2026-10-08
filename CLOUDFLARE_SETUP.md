# Настройка Cloudflare Tunnel для Lavaferret

## 1. Получение Cloudflare API credentials

### Вариант A: API Key (простой)
1. Зайдите в [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Нажмите "Profile" → "API Tokens"
3. Нажмите "View API Key" (ваш Global API Key)
4. Скопируйте ключ (начинается с `v...`)

### Вариант B: API Token (рекомендуется, более безопасный)
1. Зайдите в [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Нажмите "Profile" → "API Tokens"
3. Нажмите "Create Token"
4. Используйте шаблон "Edit Cloudflare DNS" или создайте свой:
   - **Permissions**: DNS → Edit
   - **Zone Resources**: Include → Specific Zone → ваш домен
5. Скопируйте токен (начинается с `...`)

## 2. Получение Zone ID

1. Откройте ваш домен в Cloudflare Dashboard
2. Нажмите "DNS" → "Records"
3. Zone ID указан вверху страницы (или в URL: `dash.cloudflare.com/<ZONE_ID>/...`)
4. Скопируйте Zone ID

## 3. Настройка в Lavaferret

### Способ A: Через переменные окружения (рекомендуется)

```bash
export CLOUDFLARE_API_KEY='your-api-key-or-token'
export CLOUDFLARE_EMAIL='your-email@example.com'  # Только для API Key
export CLOUDFLARE_ZONE_ID='your-zone-id'
export CLOUDFLARE_DOMAIN='example.com'  # Ваш домен без поддомена

# Запуск
python app.py
```

### Способ B: Через .env файл

Создайте файл `.env` в корне проекта:

```env
CLOUDFLARE_API_KEY=your-api-key-or-token
CLOUDFLARE_EMAIL=your-email@example.com
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_DOMAIN=example.com
```

Запустите с dotenv:
```bash
pip install python-dotenv
python app.py
```

## 4. Как это работает

1. **Настройка Cloudflare** (кнопка "Настроить Cloudflare"):
   - Создаёт CNAME запись: `server-name.example.com` → `server-name.cfargotunnel.com`
   - Устанавливает cloudflared на удалённый сервер
   - Создаёт конфигурацию для проброса портов

2. **Запуск Tunnel** (кнопка "Запустить Tunnel"):
   - Запускает `cloudflared tunnel run` на удалённом сервере
   - Cloudflare автоматически маршрутизирует трафик

3. **Подключение**:
   - Minecraft: `server-name.example.com:25565`
   - RCON: `server-name.example.com:25575`
   - Query: `server-name.example.com:25566`

## 5. Управление туннелем

- **Запустить Tunnel**: Запускает cloudflared на сервере
- **Остановить Tunnel**: Останавливает cloudflared
- **Удалить**: Удаляет DNS запись и конфигурацию

## 6. Автозапуск cloudflared

Чтобы cloudflared запускался автоматически при перезагрузке сервера:

```bash
# Создайте systemd service
sudo tee /etc/systemd/system/cloudflared-tunnel.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=your-ssh-user
ExecStart=/usr/local/bin/cloudflared --config /home/your-ssh-user/minecraft_servers/server-name/cloudflared/config.yml tunnel run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Включите и запустите
sudo systemctl enable cloudflared-tunnel
sudo systemctl start cloudflared-tunnel
```

## 7. Troubleshooting

### Ошибка "Cloudflare API credentials not configured"
- Проверьте переменные окружения
- Убедитесь, что API Key/Token валиден

### Ошибка "Tunnel failed to start"
- Проверьте логи: `ssh user@host "tail -n 20 /home/user/minecraft_servers/server-name/cloudflared/tunnel.log"`
- Убедитесь, что cloudflared установлен: `ssh user@host "which cloudflared"`

### DNS не обновляется
- Подождите до 300 секунд (TTL=1, но может быть кэширование)
- Проверьте DNS записи в Cloudflare Dashboard

### Порт не доступен
- Убедитесь, что Minecraft сервер запущен
- Проверьте firewall на удалённом сервере
- Убедитесь, что port forwarding настроен правильно

## 8. Безопасность

- Используйте API Token вместо API Key (ограниченные права)
- Не коммитьте `.env` в Git
- Регулярно обновляйте cloudflared: `sudo cloudflared update`
