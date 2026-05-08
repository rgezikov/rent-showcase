#!/usr/bin/env bash
# Run once as root on a fresh Hetzner Ubuntu 24.04 LTS server.
# Usage: bash server-setup.sh <deploy_user> <domain>
# Example: bash server-setup.sh deploy rent-showcase.fi
set -euo pipefail

DEPLOY_USER="${1:?Usage: $0 <deploy_user> <domain>}"
DOMAIN="${2:?Usage: $0 <deploy_user> <domain>}"

echo "==> Creating deploy user: $DEPLOY_USER"
if ! id "$DEPLOY_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" "$DEPLOY_USER"
    usermod -aG sudo "$DEPLOY_USER"
fi

echo "==> Copying SSH authorized_keys to $DEPLOY_USER"
mkdir -p "/home/$DEPLOY_USER/.ssh"
cp /root/.ssh/authorized_keys "/home/$DEPLOY_USER/.ssh/authorized_keys"
chown -R "$DEPLOY_USER:$DEPLOY_USER" "/home/$DEPLOY_USER/.ssh"
chmod 700 "/home/$DEPLOY_USER/.ssh"
chmod 600 "/home/$DEPLOY_USER/.ssh/authorized_keys"

echo "==> Hardening SSH"
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload ssh

echo "==> Configuring UFW firewall"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "==> Installing Docker"
apt-get update -qq
apt-get install -y --no-install-recommends ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -qq
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
usermod -aG docker "$DEPLOY_USER"
systemctl enable --now docker

echo "==> Creating application directories"
APP_DIR="/opt/rent-showcase"
mkdir -p "$APP_DIR"/{media,staticfiles,backups,nginx/certs}
chown -R "$DEPLOY_USER:$DEPLOY_USER" "$APP_DIR"

echo "==> Installing backup cron job"
BACKUP_SCRIPT="/opt/rent-showcase/scripts/db-backup.sh"
mkdir -p "$(dirname "$BACKUP_SCRIPT")"

# The backup script will be deployed with the repo; install the cron entry now.
CRON_LINE="0 3 * * * $DEPLOY_USER $BACKUP_SCRIPT >> /var/log/rent-showcase-backup.log 2>&1"
if ! grep -qF "db-backup.sh" /etc/crontab; then
    echo "$CRON_LINE" >> /etc/crontab
fi

echo ""
echo "==> Done. Next steps:"
echo "    1. Log in as $DEPLOY_USER (root login is now disabled)"
echo "    2. Point DNS A record for $DOMAIN to this server's IP"
echo "    3. Clone the repo to $APP_DIR and follow Phase 11 deployment steps"
