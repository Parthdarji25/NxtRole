#!/usr/bin/env bash
# Installs Docker Engine and Docker Compose inside Ubuntu on WSL 2 (D-041).
# Steps follow https://docs.docker.com/engine/install/ubuntu/ and
# https://docs.docker.com/engine/install/linux-postinstall/ (read on 27 Nov 2026).
#
# Run it yourself, inside the Ubuntu terminal:
#   sudo bash "/mnt/c/Users/<you>/.../NxtRole/scripts/install-docker-ubuntu.sh"
#
# Note: the last steps add your Linux user to the "docker" group so you do not need sudo for every
# command. Docker's documentation warns that this group has root-level power inside Ubuntu.

set -euo pipefail

if [ "$(id -u)" -ne 0 ] || [ -z "${SUDO_USER:-}" ]; then
  echo "Please run this with sudo from your normal Ubuntu user." >&2
  exit 1
fi

echo "== 1/5 Removing unofficial Docker packages, if any"
# shellcheck disable=SC2046
apt-get remove -y $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc \
  docker-buildx podman-docker containerd runc 2>/dev/null | cut -f1) || true

echo "== 2/5 Adding Docker's official package source"
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
apt-get update

echo "== 3/5 Installing Docker Engine and Compose"
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "== 4/5 Starting Docker now and on every start of Ubuntu"
systemctl enable --now docker.service containerd.service

echo "== 5/5 Letting '${SUDO_USER}' run docker without sudo"
groupadd --force docker
usermod -aG docker "${SUDO_USER}"
docker run --rm hello-world

echo
echo "Done. Docker version: $(docker --version)"
echo "Now close this Ubuntu window, then run 'wsl --shutdown' in PowerShell."
