#!/bin/bash
set -e

# System dependencies required by build123d (OpenCASCADE)
apt install -y libgl1 libxrender1 libxext6 libsm6 libice6 fonts-dejavu fontconfig

# Microsoft core fonts (includes Impact) — pre-accept EULA for non-interactive install
echo "ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true" | debconf-set-selections
apt install -y ttf-mscorefonts-installer

# Install uv for the current user
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"

# Install Python dependencies
cd /opt/labelmaker
uv sync
