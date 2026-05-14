#!/bin/bash
# Runs inside the LXC. Handles both fresh install and update.
set -e

REPO="https://github.com/sophof/Labelmaker.git"
INSTALL_DIR="/opt/labelmaker"

# --- System dependencies ---
apt-get update -qq
apt-get install -y -qq \
  git curl \
  libgl1 libxrender1 libxext6 libsm6 libice6 \
  fonts-dejavu fontconfig

# Microsoft core fonts (includes Impact) — pre-accept EULA
echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections
apt-get install -y -qq ttf-mscorefonts-installer

# --- uv ---
if ! command -v uv &>/dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

# --- Clone or update ---
if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Updating existing installation..."
  git -C "$INSTALL_DIR" pull
else
  echo "Cloning repository..."
  git clone "$REPO" "$INSTALL_DIR"
fi

# --- Python dependencies ---
cd "$INSTALL_DIR"
uv sync

# --- Console auto-login ---
mkdir -p /etc/systemd/system/container-getty@1.service.d
cat > /etc/systemd/system/container-getty@1.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear --keep-baud tty%I
EOF
systemctl daemon-reload

# --- Systemd service ---
cat > /etc/systemd/system/labelmaker.service << 'EOF'
[Unit]
Description=Label Maker
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/labelmaker
ExecStart=/opt/labelmaker/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable labelmaker

if systemctl is-active --quiet labelmaker; then
  systemctl restart labelmaker
else
  systemctl start labelmaker
fi

# --- 'update' command ---
cat > /usr/bin/update << 'EOF'
#!/bin/bash
set -e
cd /opt/labelmaker
echo "Pulling latest changes..."
git pull
echo "Syncing dependencies..."
"$HOME/.local/bin/uv" sync
echo "Restarting service..."
systemctl restart labelmaker
echo "Labelmaker updated."
EOF
chmod +x /usr/bin/update

echo ""
echo "Labelmaker is running on port 8000."
