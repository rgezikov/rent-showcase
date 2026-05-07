# Rent Showcase — Development Phases

> Test coverage for each phase is tracked in [DEV-TEST.md](DEV-TEST.md).  
> All new features must be covered with tests before the phase is considered complete.

## Phase 0: Local Development Environment
- Install Docker and Docker Compose on the local machine
- Create `docker-compose.yml` with services: `app`, `db` (PostgreSQL), `nginx`
- Create `docker-compose.override.yml` for dev-specific settings (code volume mount, debug mode, no SSL)
- `Dockerfile` for the Django app (based on Python slim image, uses `uv` for dependencies)
- `.env.dev` for local environment variables
- Tailwind CSS watch mode running inside the app container
- Verify full stack runs locally with `docker compose up`
- Document local development workflow (start, stop, run migrations, access shell, run tests)

## Phase 1: Project Foundation
- Django project scaffold (split settings: base / dev / prod)
- PostgreSQL configuration
- Tailwind CSS + HTMX setup
- Base template (navbar, footer, language switcher, notification bell placeholder)
- Responsive layout skeleton
- `python-decouple` for environment variables (`.env`)
- WhiteNoise for static files
- Django i18n middleware wired up (locale switching, `locale/` structure)

## Phase 2: User Accounts
→ *Tests: [DEV-TEST.md Phase 1](DEV-TEST.md#phase-1-setup--accounts--listings)*

- Custom user model (account type, company name, name, email, phone, location, avatar, bio)
- Registration and login/logout
- Email verification via Brevo
- Profile view and edit
- Account deletion (GDPR erasure)
- Profile visibility rules (logged-out users cannot view profiles)

## Phase 3: Listings
→ *Tests: [DEV-TEST.md Phase 1](DEV-TEST.md#phase-1-setup--accounts--listings)*

- Category model and fixtures (initial category list)
- Listing CRUD (create, edit, deactivate, delete)
- Auto-accept option per listing (checkbox + predefined message field)
- Multiple photo upload
- Listing detail page
- Browse and search (by category, location, keyword)
- Availability calendar (owner marks blocked dates)
- Logged-out users see listings but not owner contact details

## Phase 4: Bookings
→ *Tests: [DEV-TEST.md Phase 2](DEV-TEST.md#phase-2-bookings)*

- Booking request form (date range + optional note)
- Availability conflict check (no overlapping bookings)
- Auto-accept logic: confirm immediately + post predefined message if listing has auto-accept enabled
- Booking status flow: pending → confirmed / rejected → completed / cancelled
- Booking detail page (visible to both parties)
- Price calculation based on date range and listing rates

## Phase 5: Messaging
→ *Tests: [DEV-TEST.md Phase 3](DEV-TEST.md#phase-3-messaging)*

- Per-booking message thread
- Send and display messages
- Personal data disclaimer in thread UI

## Phase 6: Notifications
→ *Tests: [DEV-TEST.md Phase 4](DEV-TEST.md#phase-4-notifications)*

- Notification model (event type, recipient, related object, read flag)
- Triggers: new booking request, confirmed, rejected, cancelled, new message
- Bell icon with unread count badge in navbar
- Notification log page
- Mark as read (individual and all)

## Phase 7: Administration
→ *Tests: [DEV-TEST.md Phase 5](DEV-TEST.md#phase-5-administration--static-pages)*

- Django admin configuration for all models
- User blocking/banning (`is_active = False`)
- Listing moderation (deactivate/delete)

## Phase 8: Static Pages & Legal
→ *Tests: [DEV-TEST.md Phase 5](DEV-TEST.md#phase-5-administration--static-pages)*

- About page (EN + FI)
- Help page — two sections: how to rent, how to list (EN + FI)
- Privacy policy page (EN + FI)
- Terms of service page (EN + FI)
- Account deletion flow (triggered from profile settings)
- Data retention: define and document policy

## Phase 9: Translations
→ *Tests: [DEV-TEST.md Phase 6](DEV-TEST.md#phase-6-translations)*

- Mark all UI strings with `{% trans %}` / `gettext`
- Finnish `.po` translation file (`locale/fi/`)
- Language switcher functional
- Verify all pages render correctly in both languages

## Phase 10: Server Setup
- Provision Hetzner VPS (Ubuntu LTS)
- Initial server hardening: create non-root user, disable root SSH login, configure UFW firewall
- Install Docker and Docker Compose on the server
- Configure domain / subdomain DNS records
- Set up media and static file directories with correct permissions
- Basic automated database backup (cron + `docker exec pg_dump`)

## Phase 11: Deployment
- Clone repository on server
- Create `.env.prod` with production settings (DEBUG=False, ALLOWED_HOSTS, SECRET_KEY, database, Brevo SMTP)
- Obtain SSL certificate via Let's Encrypt (Certbot) — can run in its own container or on the host
- Start stack with `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- Run migrations inside the app container
- Test full stack end-to-end on production URL
