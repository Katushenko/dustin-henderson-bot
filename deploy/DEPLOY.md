# Деплой бота на сервер 83.147.222.86

## Требования к серверу
- Ubuntu 20.04 / 22.04 (или любой Debian-based)
- Root-доступ по SSH
- Python 3.10+

---

## Шаг 1 — Подключиться к серверу

```powershell
# В PowerShell на вашем компьютере:
ssh root@83.147.222.86
```

---

## Шаг 2 — Создать пользователя для бота

На сервере выполнить от root:

```bash
# Создать системного пользователя без пароля и логина
useradd --system --shell /bin/bash --home /opt/dustinbot --create-home dustinbot

# Убедиться что создан:
id dustinbot
```

> Системный пользователь (`--system`) не может логиниться по SSH и не имеет пароля.
> Это изолирует бота — даже если его взломают, доступа к системе нет.

---

## Шаг 3 — Установить зависимости системы

```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv
```

---

## Шаг 4 — Загрузить файлы бота

**На вашем компьютере (в PowerShell):**

```powershell
# Создать архив из папки бота
Compress-Archive -Path "C:\Users\1\Documents\Claude\DustinBot\*" `
    -DestinationPath "C:\Users\1\Documents\Claude\dustinbot.zip"

# Загрузить на сервер через scp
scp C:\Users\1\Documents\Claude\dustinbot.zip root@83.147.222.86:/tmp/
```

**Обратно на сервере:**

```bash
cd /tmp
apt-get install -y unzip
unzip dustinbot.zip -d dustinbot_upload

# Скопировать файлы в директорию бота
cp /tmp/dustinbot_upload/dustin_bot.py    /opt/dustinbot/
cp /tmp/dustinbot_upload/requirements.txt /opt/dustinbot/

chown -R dustinbot:dustinbot /opt/dustinbot/
```

---

## Шаг 5 — Настроить виртуальное окружение Python

```bash
# Переключиться в пользователя бота
su - dustinbot

# Создать venv и установить пакеты
python3 -m venv /opt/dustinbot/venv
/opt/dustinbot/venv/bin/pip install --upgrade pip
/opt/dustinbot/venv/bin/pip install -r /opt/dustinbot/requirements.txt

# Выйти обратно в root
exit
```

---

## Шаг 6 — Создать файл с секретами

```bash
cat > /opt/dustinbot/.env <<'EOF'
TELEGRAM_BOT_TOKEN=СЮДА_ВСТАВИТЬ_ТОКЕН_БОТА
ANTHROPIC_API_KEY=СЮДА_ВСТАВИТЬ_КЛЮЧ_ANTHROPIC
EOF

# Права только для владельца — никто другой не прочитает
chown dustinbot:dustinbot /opt/dustinbot/.env
chmod 600 /opt/dustinbot/.env
```

Открыть для редактирования:
```bash
nano /opt/dustinbot/.env
```

---

## Шаг 7 — Создать systemd-сервис

```bash
cat > /etc/systemd/system/dustinbot.service <<'EOF'
[Unit]
Description=Dustin Henderson Telegram Bot
After=network.target

[Service]
Type=simple
User=dustinbot
WorkingDirectory=/opt/dustinbot
EnvironmentFile=/opt/dustinbot/.env
ExecStart=/opt/dustinbot/venv/bin/python /opt/dustinbot/dustin_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable dustinbot
```

---

## Шаг 8 — Запустить бота

```bash
systemctl start dustinbot

# Проверить статус:
systemctl status dustinbot

# Смотреть логи в реальном времени:
journalctl -u dustinbot -f
```

Если всё хорошо, в логах будет:
```
Dustin Henderson bot is running! Holy mother of God! 🧢
```

---

## Управление ботом

| Действие | Команда |
|---|---|
| Запустить | `systemctl start dustinbot` |
| Остановить | `systemctl stop dustinbot` |
| Перезапустить | `systemctl restart dustinbot` |
| Статус | `systemctl status dustinbot` |
| Логи (live) | `journalctl -u dustinbot -f` |
| Логи (последние 50) | `journalctl -u dustinbot -n 50` |

---

## Обновление бота

```powershell
# На вашем компьютере — загрузить новый файл:
scp C:\Users\1\Documents\Claude\DustinBot\dustin_bot.py root@83.147.222.86:/opt/dustinbot/
```

```bash
# На сервере — перезапустить:
chown dustinbot:dustinbot /opt/dustinbot/dustin_bot.py
systemctl restart dustinbot
```

---

## Быстрый деплой (всё одной командой)

```bash
# На сервере, от root — запустить скрипты из папки deploy/:
bash setup_user.sh
# ... загрузить файлы ...
bash install_bot.sh
```
