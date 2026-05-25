#!/bin/bash
# Run as root: bash install_bot.sh
set -e

BOT_USER="dustinbot"
BOT_DIR="/opt/dustinbot"
SERVICE_NAME="dustinbot"

echo "=== Copying bot files ==="
cp -r /tmp/dustinbot_upload/* "$BOT_DIR/"
chown -R "$BOT_USER":"$BOT_USER" "$BOT_DIR"

echo "=== Setting up Python virtual environment ==="
sudo -u "$BOT_USER" python3 -m venv "$BOT_DIR/venv"
sudo -u "$BOT_USER" "$BOT_DIR/venv/bin/pip" install --upgrade pip -q
sudo -u "$BOT_USER" "$BOT_DIR/venv/bin/pip" install -r "$BOT_DIR/requirements.txt" -q

echo "=== Creating secrets file ==="
if [ ! -f "$BOT_DIR/.env" ]; then
    cat > "$BOT_DIR/.env" <<'EOF'
TELEGRAM_BOT_TOKEN=PASTE_YOUR_TOKEN_HERE
ANTHROPIC_API_KEY=PASTE_YOUR_KEY_HERE
EOF
    chown "$BOT_USER":"$BOT_USER" "$BOT_DIR/.env"
    chmod 600 "$BOT_DIR/.env"
    echo "Created $BOT_DIR/.env — EDIT IT before starting the bot!"
else
    echo ".env already exists, skipping."
fi

echo "=== Installing systemd service ==="
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Dustin Henderson Telegram Bot
After=network.target

[Service]
Type=simple
User=${BOT_USER}
WorkingDirectory=${BOT_DIR}
EnvironmentFile=${BOT_DIR}/.env
ExecStart=${BOT_DIR}/venv/bin/python ${BOT_DIR}/dustin_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit secrets:  nano $BOT_DIR/.env"
echo "  2. Start bot:     systemctl start $SERVICE_NAME"
echo "  3. Check status:  systemctl status $SERVICE_NAME"
echo "  4. Watch logs:    journalctl -u $SERVICE_NAME -f"
