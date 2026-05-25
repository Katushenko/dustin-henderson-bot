# 🧢 Dustin Henderson Telegram Bot

Telegram-бот с характером Дастина Хендерсона из сериала **Stranger Things**, работающий на Claude AI.

Бот отвечает в образе персонажа — на русском и английском языке, знает всё про Изнанку, D&D, Cerebro и друзей из Хокинса.

---

## Быстрый старт

### Что понадобится
- Сервер с Ubuntu 20.04 / 22.04
- Токен Telegram-бота — получить у [@BotFather](https://t.me/BotFather)
- API-ключ Anthropic — получить на [console.anthropic.com](https://console.anthropic.com)

---

## Установка на сервер

### 1. Подключиться к серверу
```bash
ssh root@ВАШ_IP
```

### 2. Создать пользователя для бота
```bash
useradd --system --shell /bin/bash --home /opt/dustinbot --create-home dustinbot
```
> Системный пользователь без пароля и SSH-доступа — бот изолирован от системы.

### 3. Установить зависимости
```bash
apt-get update
apt-get install -y python3 python3-pip python3-venv
```

### 4. Скачать файлы бота
```bash
cd /opt/dustinbot
apt-get install -y git
git clone https://github.com/Katushenko/dustin-henderson-bot.git .
chown -R dustinbot:dustinbot /opt/dustinbot
```

### 5. Создать виртуальное окружение и установить пакеты
```bash
sudo -u dustinbot python3 -m venv /opt/dustinbot/venv
sudo -u dustinbot /opt/dustinbot/venv/bin/pip install --upgrade pip
sudo -u dustinbot /opt/dustinbot/venv/bin/pip install -r /opt/dustinbot/requirements.txt
```

### 6. Создать файл с токенами
```bash
cat > /opt/dustinbot/.env <<'EOF'
TELEGRAM_BOT_TOKEN=ВАШ_ТОКЕН_БОТА
ANTHROPIC_API_KEY=ВАШ_КЛЮЧ_ANTHROPIC
EOF

chown dustinbot:dustinbot /opt/dustinbot/.env
chmod 600 /opt/dustinbot/.env
```

### 7. Создать systemd-сервис
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

### 8. Запустить бота
```bash
systemctl start dustinbot
systemctl status dustinbot
```

Если всё хорошо, в логах появится:
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

```bash
cd /opt/dustinbot
git pull
systemctl restart dustinbot
```

---

## Команды бота

| Команда | Действие |
|---|---|
| `/start` | Начать разговор с Дастином |
| `/reset` | Сбросить историю и начать заново |
| `/help` | Список команд |

---

## Возможности

- **Образ персонажа** — восклицания, шепелявость, хвастовство, упоминания Сузи, шляпы Сесиля, Cerebro и D&D
- **Знания из сериала** — Изнанка, Демогоргон, Дарт, Разрушитель разума, Старкорт, все друзья
- **Двуязычность** — автоматически отвечает на языке пользователя (RU/EN), переключение на лету
- **Быстрые кнопки** — 8 кнопок с темами для старта разговора
- **Память диалога** — хранит последние 30 сообщений на пользователя
- **Автоперезапуск** — systemd перезапускает бота при сбое или перезагрузке сервера
