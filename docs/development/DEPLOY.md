# Rent Showcase — Deployment Runbook

## Infrastructure

| Item | Value |
|---|---|
| Server | Hetzner CX23 — 2 vCPU, 4 GB RAM, 40 GB SSD |
| OS | Ubuntu 24.04 LTS |
| IP | 135.181.98.212 |
| Domain | rent.respobit.eu |
| App directory | `/opt/rent-showcase/` |
| Deploy user | `deploy` |
| SSL | Let's Encrypt, auto-renewed by Certbot |

---

## Routine deploy (code change)

```bash
ssh deploy@rent.respobit.eu "bash /opt/rent-showcase/scripts/deploy.sh"
```

This does: `git pull` → `docker compose up -d --build app` → prints container status.

> **Important:** Always use `up -d --build`, never `restart`. The `restart` command does not re-read the env file or rebuild the image.

---

## First-time server setup

Run once as root on a fresh Ubuntu 24.04 VPS:

```bash
ssh root@<server-ip> 'bash -s' < scripts/server-setup.sh deploy rent.respobit.eu
```

This creates the `deploy` user, copies SSH keys, disables root login, configures UFW (ports 22/80/443), installs Docker, creates `/opt/rent-showcase/` directories, and registers the backup cron job.

After the script completes, root SSH login is disabled. Use `deploy` for all further access.

---

## First-time deployment

### 1. Clone the repository

```bash
ssh deploy@rent.respobit.eu
git clone https://github.com/rgezikov/rent-showcase.git /tmp/rent-showcase
sudo cp -a /tmp/rent-showcase/. /opt/rent-showcase/
rm -rf /tmp/rent-showcase
```

### 2. Create `.env.prod`

```bash
cat > /opt/rent-showcase/.env.prod << 'EOF'
DJANGO_SETTINGS_MODULE=config.settings.prod
DEBUG=False
SECRET_KEY=<generate with: python3 -c "import secrets; print(secrets.token_urlsafe(50))">
ALLOWED_HOSTS=rent.respobit.eu

DB_NAME=rent_showcase
DB_USER=rent_user
DB_PASSWORD=<strong random password>
DB_HOST=db
DB_PORT=5432

BREVO_SMTP_HOST=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_USER=<brevo smtp login>
BREVO_SMTP_PASSWORD=<brevo smtp key>
DEFAULT_FROM_EMAIL=noreply@rent.respobit.eu
EOF

ln -s .env.prod /opt/rent-showcase/.env
```

### 3. Obtain SSL certificate

Run before starting nginx (port 80 must be free):

```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d rent.respobit.eu \
  --non-interactive --agree-tos -m <your-email>
sudo cp /etc/letsencrypt/live/rent.respobit.eu/fullchain.pem /opt/rent-showcase/nginx/certs/
sudo cp /etc/letsencrypt/live/rent.respobit.eu/privkey.pem /opt/rent-showcase/nginx/certs/
sudo chown deploy:deploy /opt/rent-showcase/nginx/certs/*.pem
```

Certbot sets up automatic renewal. After renewal, certs must be re-copied to `nginx/certs/`. Add a renewal hook if needed:

```bash
# /etc/letsencrypt/renewal-hooks/deploy/copy-certs.sh
cp /etc/letsencrypt/live/rent.respobit.eu/fullchain.pem /opt/rent-showcase/nginx/certs/
cp /etc/letsencrypt/live/rent.respobit.eu/privkey.pem /opt/rent-showcase/nginx/certs/
docker compose -f /opt/rent-showcase/docker-compose.yml \
               -f /opt/rent-showcase/docker-compose.prod.yml restart nginx
```

### 4. Start the stack

```bash
cd /opt/rent-showcase
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Migrations, `collectstatic`, and category fixture load automatically via `entrypoint.sh`.

### 5. Create superuser

```bash
ssh -t deploy@rent.respobit.eu \
  "docker exec -it rent-showcase-app-1 uv run python manage.py createsuperuser"
```

---

## Brevo email setup

Transactional email uses Brevo SMTP. For emails to deliver, the sending domain must be authenticated.

### DNS records required for `rent.respobit.eu`

| Type | Name | Value |
|---|---|---|
| TXT | `@` (respobit.eu) | `v=spf1 +a +mx +a:fi8.hostaan.fi include:spf.brevo.com ~all` |
| TXT | `@` (respobit.eu) | `brevo-code:<code from Brevo>` |
| CNAME | `brevo1._domainkey.respobit.eu` | `b1.respobit-eu.dkim.brevo.com` |
| CNAME | `brevo2._domainkey.respobit.eu` | `b2.respobit-eu.dkim.brevo.com` |
| TXT | `_dmarc.respobit.eu` | `v=DMARC1; p=quarantine; adkim=r; aspf=r; rua=mailto:rua@dmarc.brevo.com` |

And for the sending subdomain `rent.respobit.eu` specifically (separate domain authentication in Brevo):

| Type | Name | Value |
|---|---|---|
| CNAME | `brevo1._domainkey.rent.respobit.eu` | *(from Brevo domain setup)* |
| CNAME | `brevo2._domainkey.rent.respobit.eu` | *(from Brevo domain setup)* |

**Notes:**
- SPF must be a single record — combine with existing SPF rather than adding a second.
- DKIM CNAME records will show "does not resolve to A/AAAA" warnings — this is normal and expected.
- After adding DNS records, click **Verify** in Brevo (Senders & IP → Domains). Propagation takes 5–30 minutes.
- The sender `noreply@rent.respobit.eu` must be added and verified in Brevo (Senders & IP → Senders).

### Test email delivery

```bash
ssh deploy@rent.respobit.eu "docker exec rent-showcase-app-1 uv run python -c \"
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.prod'
django.setup()
from django.core.mail import send_mail
send_mail('Test', 'Test body', 'noreply@rent.respobit.eu', ['your@email.com'])
print('OK')
\""
```

---

## Database backup

Automated via cron (installed by `server-setup.sh`):
- **Schedule:** daily at 03:00
- **Script:** `/opt/rent-showcase/scripts/db-backup.sh`
- **Output:** `/opt/rent-showcase/backups/db_YYYYMMDD_HHMMSS.sql.gz`
- **Retention:** 30 days

Run manually:
```bash
ssh deploy@rent.respobit.eu "bash /opt/rent-showcase/scripts/db-backup.sh"
```

Restore from backup:
```bash
ssh deploy@rent.respobit.eu
gunzip -c /opt/rent-showcase/backups/db_<timestamp>.sql.gz | \
  docker exec -i rent-showcase-db-1 psql -U rent_user rent_showcase
```

---

## Useful commands

```bash
# View live app logs
ssh deploy@rent.respobit.eu "docker logs -f rent-showcase-app-1"

# Container status
ssh deploy@rent.respobit.eu "docker compose -f /opt/rent-showcase/docker-compose.yml \
  -f /opt/rent-showcase/docker-compose.prod.yml ps"

# Django shell
ssh deploy@rent.respobit.eu "docker exec -it rent-showcase-app-1 uv run python manage.py shell"

# Run migrations manually
ssh deploy@rent.respobit.eu "docker exec rent-showcase-app-1 uv run python manage.py migrate"
```
