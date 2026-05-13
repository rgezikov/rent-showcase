# Rent Showcase — Development Phases

> Test coverage for each phase is tracked in [DEV-TEST.md](DEV-TEST.md).  
> All new features must be covered with tests before the phase is considered complete.

## Phase 0: Local Development Environment ✓
- Docker Compose stack: `app`, `db` (PostgreSQL), `tailwind` watch container
- `docker-compose.override.yml` for dev (code volume mount, debug mode, browser-reload, no SSL)
- `Dockerfile` multi-stage: `css-builder` → `base` → `dev` / `prod`
- `.env` / `.env.example` for local environment variables
- Tailwind CSS watch mode in dedicated container
- `uv` for Python dependency management (`pyproject.toml`, `uv.lock`)

## Phase 1: Project Foundation ✓
- Django 5.2 project scaffold with split settings (`base` / `dev` / `test` / `prod`)
- PostgreSQL configuration via `python-decouple`
- Tailwind CSS + HTMX setup
- Base template (navbar, footer, language switcher, notification bell)
- Responsive layout skeleton
- WhiteNoise for static files
- Django i18n middleware wired up (`LocaleMiddleware`, `locale/` structure)

## Phase 2: User Accounts ✓
→ *Tests: [DEV-TEST.md Phase 1](DEV-TEST.md#phase-1-setup--accounts--listings)*

- Custom user model (`AbstractUser`) with account type, company name, name, email, phone, location, avatar, bio
- Registration with email verification (signed token, Brevo SMTP)
- Login / logout
- Profile view and edit
- Account deletion (GDPR erasure)
- Profile visibility: logged-out users cannot view profiles

## Phase 3: Listings ✓
→ *Tests: [DEV-TEST.md Phase 1](DEV-TEST.md#phase-1-setup--accounts--listings)*

- `Category` model with fixture (9 categories, loaded automatically on container start)
- Listing CRUD (create, edit, deactivate, delete)
- Auto-accept option per listing (checkbox + predefined message field)
- Multiple photo upload (custom `MultipleFileField`)
- Listing detail page with availability calendar (flatpickr, disabled dates via JSON)
- Browse and search (by category, location, keyword, date range)
- Logged-out users see listings but not owner contact details

## Phase 4: Bookings ✓
→ *Tests: [DEV-TEST.md Phase 2](DEV-TEST.md#phase-2-bookings)*

- Booking request form (date range + optional note)
- Availability conflict check (no overlapping confirmed bookings)
- Auto-accept: confirm immediately + post predefined message
- Booking status flow: `pending` → `confirmed` / `rejected` → `completed` / `cancelled`
- Booking detail page (visible to both parties)
- Price calculation based on date range and listing rates (daily / weekend / weekly / monthly + base fee)

## Phase 5: Messaging ✓
→ *Tests: [DEV-TEST.md Phase 3](DEV-TEST.md#phase-3-messaging)*

- Per-booking message thread
- Send and display messages
- Personal data disclaimer in thread UI

## Phase 6: Notifications ✓
→ *Tests: [DEV-TEST.md Phase 4](DEV-TEST.md#phase-4-notifications)*

- `Notification` model (event type, recipient, booking FK, read flag)
- Triggers: new request, confirmed, rejected, cancelled, new message
- Bell icon with unread count badge in navbar (context processor)
- Badge updates live via HTMX polling (`/notifications/unread-count/`) every 10s — no page refresh
- Message thread on booking detail also polls every 10s for new messages
- Notification list page
- Mark as read (individual and all)

## Phase 7: Administration ✓
→ *Tests: [DEV-TEST.md Phase 5](DEV-TEST.md#phase-5-administration--static-pages)*

- Django admin for all models with custom actions
- User block/unblock (`is_active` toggle), listing deactivate/activate
- `SiteSettings` singleton model — registration open/closed toggle (admin-controlled)

## Phase 16: Per-user limits

- `SiteSettings` gains `max_active_listings` (default 20) and `max_pending_bookings` (default 10)
- `User` gains `max_active_listings_override` and `max_pending_bookings_override` (nullable — blank = use site default)
- `User.get_max_active_listings()` / `get_max_pending_bookings()` resolve per-user override → site default
- `listing_create` view checks active listing count before allowing creation
- `booking_create` view checks pending booking count before allowing submission
- Both limits exposed in Django admin: site defaults in Site Settings, per-user overrides in User edit

## Phase 8: Translations ✓
→ *Tests: [DEV-TEST.md Phase 6](DEV-TEST.md#phase-6-translations)*

- All UI strings marked with `{% trans %}` / `gettext`
- Finnish `.po` file (`locale/fi/LC_MESSAGES/django.po`) — 244 strings including 9 category names
- `.mo` files compiled at Docker image build time (`RUN manage.py compilemessages`)
- `gettext` installed in Docker image (`apt-get install gettext`)
- Language switcher functional; selection stored in session

## Phase 9: Static Pages ✓
→ *Tests: [DEV-TEST.md Phase 5](DEV-TEST.md#phase-5-administration--static-pages)*

- About, Help, Privacy Policy, Terms of Service — all bilingual (EN + FI)
- Bilingual prose pages use `{% get_current_language %}` + `{% if lang == 'fi' %}` pattern
- Footer links wired to all four pages

## Phase 10: Server Setup ✓
- Hetzner CX23 VPS provisioned (Ubuntu 24.04 LTS, Helsinki, 2 vCPU / 4 GB RAM / 40 GB SSD)
- `scripts/server-setup.sh` automates: deploy user creation, SSH hardening (root login disabled, key-only), UFW firewall (SSH/80/443), Docker install, `/opt/rent-showcase/` directory structure, backup cron entry
- Domain: `rent.respobit.eu` → A record → `135.181.98.212`
- DB backup cron: `scripts/db-backup.sh` runs daily at 03:00, gzipped pg_dump, 30-day retention

## Phase 11: Deployment ✓
- Repo cloned to `/opt/rent-showcase/` on server
- `.env.prod` created on server (not in git): `DJANGO_SETTINGS_MODULE=config.settings.prod`, `SECRET_KEY`, `ALLOWED_HOSTS`, DB credentials, Brevo SMTP
- SSL certificate obtained via Certbot standalone (before nginx starts): `certbot certonly --standalone -d rent.respobit.eu`
- Certs copied to `nginx/certs/` — auto-renewal configured by Certbot
- Stack started: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
- Migrations and `collectstatic` run automatically via `entrypoint.sh`
- Categories loaded automatically via `entrypoint.sh` (`loaddata listings/fixtures/categories.json`)
- One-command deploy: `bash /opt/rent-showcase/scripts/deploy.sh`
- Brevo transactional email: domain `rent.respobit.eu` authenticated (SPF, DKIM via CNAME, DMARC)

## Phase 12: Google OAuth ✓
→ *Tests: [DEV-TEST.md Phase 8](DEV-TEST.md#phase-8-google-oauth)*

- Install and configure `django-allauth` with Google provider
- Create Google OAuth 2.0 credentials in Google Cloud Console; add `rent.respobit.eu` as authorised origin and callback URL
- Custom allauth adapter: set `account_type=person`, copy `given_name`/`family_name` from Google profile, skip email verification
- Add "Sign in with Google" button to login and register pages
- Display a note near the Google button: Google sign-in is for personal accounts only; companies should use the email/password form
- Google OAuth is for person accounts only — company accounts continue to use email/password
- Store Google Client ID and Secret in `.env.prod` (never in git)

## Phase 15: Extended Pricing Model ✓

- New `Listing` fields: `delivery_fee`, `deposit` (refundable, shown separately, not in rental price), `minimum_days`
- `delivery_fee` included in `Booking.calculate_price()`
- `BookingForm` validates `minimum_days` before availability check; booking form shows warning to renter
- Listing detail shows all new fields when set

## Phase 14: Email Notifications ✓

- `notifications/emails.py` — `send_notification_email(notification)` sends plain-text email via Brevo for all 5 event types
- `create_notification()` extended to call email function after saving notification
- Email body includes notification text, listing title, dates, and a direct booking link
- Domain resolved via Sites framework (set correctly by entrypoint.sh)
- `fail_silently=True` — email failures never break the booking or messaging flow

## Phase 13: Password Reset ✓
→ *Tests: [DEV-TEST.md Phase 9](DEV-TEST.md#phase-9-password-reset)*

- Django's built-in password reset flow (`PasswordResetView`, `PasswordResetConfirmView`)
- Sends reset link via Brevo SMTP (already configured)
- "Forgot password?" link on the login page
- Bilingual email templates (EN + FI) and reset pages
- Google OAuth users who have no password get a clear message that password reset is not applicable
