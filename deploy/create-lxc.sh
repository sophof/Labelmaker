#!/bin/bash
# Runs on the Proxmox host. Creates a new LXC and deploys Labelmaker inside it.
set -e

# --- Configuration ---
HOSTNAME="labelmaker"
CPU=2
RAM=2048       # MB
DISK=8         # GB
BRIDGE="vmbr0"
TMPL_STORAGE="local"   # where to store/find the CT template
REPO="https://github.com/sophof/Labelmaker.git"

# Optional: pass a CT ID as the first argument, otherwise auto-assign
CTID="${1:-}"

# --- CT ID resolution ---
if [ -z "$CTID" ]; then
  CTID=$(pvesh get /cluster/nextid)
fi

while pct status "$CTID" &>/dev/null || qm status "$CTID" &>/dev/null; do
  echo "CT ID $CTID is already taken, trying $((CTID + 1))..."
  CTID=$((CTID + 1))
done
echo "Using CT ID: $CTID"

# --- Storage selection ---
MENU_OPTIONS=()
while read -r name _type _status _total _used _avail _pct; do
  MENU_OPTIONS+=("$name" "$_avail available")
done < <(pvesm status -content rootdir | awk 'NR>1')

if [ "${#MENU_OPTIONS[@]}" -eq 0 ]; then
  echo "ERROR: No storage pools found that support container root filesystems."
  exit 1
fi

STORAGE=$(whiptail --backtitle "Labelmaker Deployment" \
  --title "Storage Selection" \
  --menu "Select storage for the container root filesystem:" \
  16 58 6 \
  "${MENU_OPTIONS[@]}" \
  3>&1 1>&2 2>&3) || { echo "Cancelled."; exit 1; }
echo "Using storage: $STORAGE"

# --- Debian 12 template ---
TEMPLATE=$(pveam list "$TMPL_STORAGE" 2>/dev/null | awk '{print $1}' | grep "debian-13" | sort -rV | head -1)

if [ -z "$TEMPLATE" ]; then
  echo "Debian 12 template not found, downloading..."
  pveam update
  TMPL_NAME=$(pveam available --section system | grep "debian-13" | sort -rV | head -1)
  if [ -z "$TMPL_NAME" ]; then
    echo "ERROR: Could not find a Debian 12 template. Run 'pveam update' and try again."
    exit 1
  fi
  pveam download "$TMPL_STORAGE" "$TMPL_NAME"
  TEMPLATE="$TMPL_STORAGE:vztmpl/$TMPL_NAME"
fi
echo "Using template: $TEMPLATE"

# --- Create container ---
echo "Creating LXC container..."
pct create "$CTID" "$TEMPLATE" \
  --hostname "$HOSTNAME" \
  --cores "$CPU" \
  --memory "$RAM" \
  --rootfs "$STORAGE:$DISK" \
  --net0 "name=eth0,bridge=$BRIDGE,ip=dhcp" \
  --unprivileged 1 \
  --features "nesting=1" \
  --ostype debian \
  --tags "3dprint" \
  --start 0

echo "Starting container..."
pct start "$CTID"

# --- Wait for network ---
echo "Waiting for network..."
for i in $(seq 1 30); do
  if pct exec "$CTID" -- bash -c "ping -c1 -W1 8.8.8.8 &>/dev/null" 2>/dev/null; then
    echo "Network ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "ERROR: Network not available after 60s. Check bridge and DHCP config."
    exit 1
  fi
  sleep 2
done

# --- Bootstrap: install git and clone repo ---
echo "Installing git..."
pct exec "$CTID" -- bash -c "apt-get update -qq && apt-get install -y -qq git"

echo "Cloning repository..."
pct exec "$CTID" -- bash -c "git clone $REPO /opt/labelmaker"

# --- Run install script ---
echo "Running install script..."
pct exec "$CTID" -- bash /opt/labelmaker/deploy/install.sh

# --- Done ---
CONTAINER_IP=$(pct exec "$CTID" -- bash -c \
  "ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'" 2>/dev/null || true)

echo ""
echo "Labelmaker deployed successfully (CT ID: $CTID)."
if [ -n "$CONTAINER_IP" ]; then
  echo "Access at: http://$CONTAINER_IP:8000"
else
  echo "Access at: http://<container-ip>:8000"
fi
