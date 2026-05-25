#!/bin/bash
# Run as root: bash setup_user.sh
set -e

BOT_USER="dustinbot"
BOT_DIR="/opt/dustinbot"

echo "=== Creating user '$BOT_USER' ==="
if id "$BOT_USER" &>/dev/null; then
    echo "User '$BOT_USER' already exists, skipping."
else
    useradd --system --shell /bin/bash --home "$BOT_DIR" --create-home "$BOT_USER"
    echo "User '$BOT_USER' created."
fi

echo "=== Installing system packages ==="
apt-get update -q
apt-get install -y python3 python3-pip python3-venv

echo "=== Creating bot directory ==="
mkdir -p "$BOT_DIR"
chown "$BOT_USER":"$BOT_USER" "$BOT_DIR"

echo ""
echo "Done! Next step: run  bash install_bot.sh  as root."
