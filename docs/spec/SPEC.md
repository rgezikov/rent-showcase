# Rent Showcase — Product Specification (MVP)

## 1. Overview

Rent Showcase is a two-sided equipment rental marketplace. It connects people and organizations that have equipment to rent out (owners) with people or organizations looking to rent equipment (renters).

---

## 2. Legal & Privacy Compliance (GDPR / Finland)

Finland is an EU member state. The service must comply with **GDPR** and the Finnish **Data Protection Act (Tietosuojalaki 1050/2018)**. The supervisory authority is the **Office of the Data Protection Ombudsman** (*Tietosuojavaltuutettu*, tietosuoja.fi).

### Lawful basis for processing
- Account and booking data: processed on the basis of **contract performance**.
- Any additional processing (e.g. analytics): requires **consent** or documented **legitimate interest**.

### Required at launch
- **Privacy policy page** — publicly accessible, shown before or at registration. Must state: what data is collected, purpose, retention period, third-party sharing, and user rights.
- **Terms of service page** — publicly accessible, outlines user obligations and platform liability limits.
- **Account deletion** — users must be able to delete their account, triggering erasure of all personal data.
- **Data retention policy** — define and enforce limits (e.g. anonymise completed booking data after 2 years; delete inactive accounts after 3 years).

### User rights to support
| Right | How |
|---|---|
| Access | User can view all their personal data |
| Rectification | User can edit their profile |
| Erasure | Account deletion removes personal data |
| Portability | User can export their data (post-MVP) |

### Data minimisation
Only collect data that is strictly necessary for the service to function. Current model (name, email, phone, location, booking history, messages) is justified by contract performance.

### Data breach notification
Must notify the Ombudsman within **72 hours** of discovering a personal data breach.

### Data storage location
All data must remain within the **EU/EEA**. Hetzner (Helsinki) satisfies this requirement.

### Cookies & analytics
If tracking or analytics are added, a **cookie consent banner** is required. For MVP, avoid third-party tracking to keep compliance simple.

### No DPO required
A Data Protection Officer is not mandatory for a small marketplace of this type.

> **Note:** This document outlines the technical and product interpretation of requirements. For definitive legal advice consult a qualified Finnish lawyer or the Ombudsman's official guidance.

---

## 3. Domain

**Equipment rental only.** Categories may include (but are not limited to): construction tools, AV/event gear, medical devices, sports equipment, and similar.

---

## 4. User Accounts

- A single account can act as both **owner** (lists equipment) and **renter** (books equipment) — no separate accounts needed.
- Authentication: email + password registration and login, or **Google OAuth** (sign in with Google).
- **Email verification required** for email/password accounts — user must confirm their email address before accessing the app.
- Google OAuth accounts are created without email verification (Google has already verified the email).
- Profile fields: account type (person / company), name, company name (only if account type is company), email, phone, location (city/area), avatar/photo, short bio.

### Google OAuth
- Available for **person accounts only** — company accounts must use email/password registration.
- Google provides first name, last name, and email — account is created automatically with `account_type=person`.
- No post-signup step required; optional profile fields (phone, location, bio, avatar) can be filled in later.
- A visible note on the login and registration pages informs users that Google sign-in is for personal accounts only; companies should use the email/password form.
- Implemented via `django-allauth`.

### Profile visibility
- **Logged-out users** can browse listings and see prices, but owner details (name, phone, email, bio) are hidden.
- **Logged-in users** can view another user's full profile: name, general location, member since date, active listings, and contact details.

### Registration toggle
- An admin-controlled toggle (`SiteSettings.registration_open`) allows registration to be disabled site-wide without a code change.

### Per-user limits
- **Max active listings** — prevents a user from creating an excessive number of listings.
- **Max pending bookings** — prevents a user from flooding owners with booking requests.
- Global defaults are set in `SiteSettings` (`max_active_listings` default: 20, `max_pending_bookings` default: 10).
- Individual overrides can be set per user in the admin (leave blank to use the site default).
- A trusted power user can be given a higher limit; a flagged account can be restricted below the default.

---

## 5. Listings

Each listing represents a piece of equipment available for rent.

### Fields
| Field | Notes |
|---|---|
| Title | Short descriptive name |
| Description | Full details |
| Category | From a predefined list |
| Photos | Multiple photos supported |
| Location | City / area (not exact address) |
| Price per day | Required |
| Price per weekend | Optional |
| Price per week | Optional |
| Price per month | Optional |
| Base fee | Optional one-time fee added to the rental price (e.g. pickup/handling fee) |
| Preferred payment methods | Free text, e.g. "cash, bank transfer" — off-platform, informational only |
| Availability calendar | Owner marks blocked/booked date ranges |
| Quantity | Number of identical units available (default 1) |
| Auto-accept bookings | Optional per listing; if enabled, qualifying requests are confirmed automatically |
| Auto-accept message | Predefined message sent automatically to the renter upon auto-acceptance |
| Active/inactive | Owner can pause a listing |

### Listing lifecycle
- Owner creates → listing is active and publicly visible.
- Owner can edit, deactivate, or delete their listing.

---

## 6. Bookings

### Availability
- Each listing has a calendar showing available and booked date ranges.
- Renters select a start date, end date, and requested quantity when submitting a booking.
- Availability check: total confirmed bookings for the date range must not exceed the listing's quantity.

### Booking flow
1. Renter submits a booking **request** (date range + optional note).
2. If the listing has **auto-accept** enabled and the dates are available → booking is confirmed immediately and the predefined message is posted in the thread. Owner is still notified.
3. Otherwise, owner receives notification and **confirms** or **rejects** the request manually.
4. If confirmed → booking becomes **active**.
5. Either party can **cancel** an active booking.
6. After the end date → booking moves to **completed**.

### Booking statuses
`pending` → `confirmed` → `completed`
`pending` → `rejected`
`confirmed` → `cancelled`

### Pricing
- Total price = base fee (if set) + (duration × applicable rate). Parties settle payment off-platform.

---

## 7. Messaging

- Each booking has its own message thread.
- Both owner and renter can send messages within the thread.
- Users are free to exchange contact details and communicate via any other channel.
- A disclaimer is shown in every message thread: *"Be cautious about sharing personal contact details with people you don't know."*
- Messages are simple text; no attachments for MVP.

---

## 8. Notifications

Each account has a personal notification log accessible from the navigation bar (bell icon with unread count badge).

### Triggering events
| Event | Recipient |
|---|---|
| New booking request received | Owner |
| Booking confirmed | Renter |
| Booking rejected | Renter |
| Booking cancelled (by other party) | Owner or Renter |
| New message in a booking thread | Owner or Renter |

### Behaviour
- Notifications are listed in reverse chronological order.
- Each notification shows: a short description, the related listing/booking, and a timestamp.
- Each notification links to the relevant page (booking detail, message thread).
- Notifications can be marked as read individually or all at once.
- Unread count is shown as a badge on the bell icon in the navbar.

### Delivery
- **In-app** — bell badge updates every 10 seconds via HTMX polling, no page refresh required.
- The message thread on the booking detail page also polls every 10 seconds for new messages.
- **Email** — a plain-text email is sent via Brevo for every notification event. Emails fail silently so delivery issues never affect the booking flow.
- Telegram notifications are a post-MVP feature.

---

## 9. Payments

- **Off-platform permanently.** No payment processing in the app.
- Price is displayed for reference; actual payment is arranged directly between owner and renter.

---

## 10. Tech Stack

| Layer | Choice |
|---|---|
| Backend | Django 5.x (Python) |
| Database | PostgreSQL |
| Frontend | Django templates + HTMX + Tailwind CSS |
| Static files | WhiteNoise (served via Django/Nginx) |
| Transactional email | Brevo (free tier — 300 emails/day) via SMTP |
| Social auth | django-allauth (Google OAuth) |
| Web server | Gunicorn + Nginx |
| Containerisation | Docker + Docker Compose |
| Hosting | Hetzner CX23 VPS (2 vCPU, 4 GB RAM, 40 GB SSD) |
| SSL | Let's Encrypt (Certbot) |
| Domain | rent.respobit.eu |

### Docker strategy
The entire stack (app, PostgreSQL, Nginx) runs in Docker Compose from local development through to production. This ensures environment parity, simplifies moving between machines, and makes clean test deployments trivial. Code is mounted as a volume in development for fast iteration. Environment-specific overrides (`docker-compose.override.yml`) handle the differences between dev and prod. All development work should be done with Docker in mind — no host-specific paths, no hardcoded ports, all config via environment variables.

---

## 11. Django App Structure

| App | Responsibility |
|---|---|
| `accounts` | Registration, login, profile management |
| `listings` | Create/edit/browse/search equipment listings, categories, photos |
| `bookings` | Booking requests, status flow, availability calendar |
| `messaging` | Per-booking message threads |
| `notifications` | Per-account notification log |

---

## 12. Responsiveness

The UI must work correctly on **desktop, tablet, and mobile** (phone). Tailwind CSS utility classes handle responsive layout.

---

## 13. Internationalisation (i18n)

- The interface is available in **English** (default) and **Finnish**.
- Language can be switched by the user at any time via a language switcher in the navigation bar.
- Django's built-in i18n framework (`gettext`) is used for all UI strings.
- Translation files are maintained as `.po`/`.mo` files under `locale/fi/`.
- `.mo` files are compiled at Docker image build time (not stored in git).
- The selected language is stored in the session (Django `LocaleMiddleware`).
- User-generated content (listing titles, descriptions, messages) is **not** translated — only the UI chrome is.
- Category names are DB-stored strings translated at runtime via `{% trans variable %}` and manually maintained in the `.po` file.

---

## 14. Static Pages

All static pages are available in English and Finnish and accessible to logged-out users. They are linked from the footer.

### About
Describes the service: what it is, who it is for, and how it works.

### Help
Two sections: how to rent equipment, and how to list equipment for rent.

### Privacy Policy
GDPR-compliant policy covering: data collected, legal basis, retention periods, data sharing, user rights, breach notification, and supervisory authority contact.

### Terms of Service
Covers: service description, user account responsibilities, rental agreement disclaimers, prohibited content, liability limits, account termination, governing law (Finnish law, Helsinki District Court).

---

## 15. Administration

- Django built-in admin panel (`/admin`) is used for MVP.
- Administrator roles are managed via Django's built-in permissions (`is_staff`, `is_superuser`).
- Administrators can: manage users, listings, categories, bookings, and messages.
- **User blocking/banning** — admin can deactivate a user account (`is_active = False`), which immediately prevents login and hides their listings.
- **Registration toggle** — admin can disable new registrations via `SiteSettings` without a code change.

---

## 16. Post MVP Features

- ~~Listing statistics for owners (views, booking requests, confirmed bookings, revenue per listing)~~ → done (Phase 18)
- ~~Extended pricing model: deposit, delivery fee, minimum rental period~~ → done (Phase 15)
- Reviews and ratings
- Email notifications (booking events, messages)
- ~~Email-based password reset~~ → done (Phase 13)
- ~~Email notifications~~ → done (Phase 14)
- Telegram notifications (may be simpler than email — via Telegram Bot API)
- ~~Data portability export~~ → done (Phase 17)
- ~~Social login (Google etc. via django-allauth)~~ → done (Phase 19)
