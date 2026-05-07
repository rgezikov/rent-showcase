# Rent Showcase — Test Plan

Testing runs in parallel with feature development. Every phase in [DEV.md](DEV.md) must have corresponding test coverage before it is considered complete.

## Stack

| Tool | Purpose |
|---|---|
| `pytest-django` | Unit tests, form validation, view/HTTP tests |
| `factory-boy` | Test data factories — no hand-crafted fixtures |
| `pytest-playwright` | End-to-end browser tests for UI and JS behaviour |
| `pytest-xdist` | Parallel test execution (`-n auto`) |

Test settings live in `config/settings/test.py`. The test database is separate from dev. Passwords use `MD5PasswordHasher` for speed.

Run all tests:
```
docker compose exec app uv run pytest
```

Run only unit tests (fast):
```
docker compose exec app uv run pytest -m "not e2e"
```

Run only e2e tests:
```
docker compose exec app uv run pytest -m e2e
```

---

## Phase 1: Setup + Accounts + Listings
*Covers [DEV.md Phase 2](DEV.md#phase-2-user-accounts) and [DEV.md Phase 3](DEV.md#phase-3-listings)*

### Infrastructure setup
- Install `pytest-django`, `factory-boy`, `pytest-playwright`, `pytest-xdist`
- `pytest.ini` / `pyproject.toml` configuration pointing at test settings
- `config/settings/test.py` (fast hasher, separate DB, console email backend)
- `UserFactory`, `ListingFactory`, `CategoryFactory`, `ListingPhotoFactory`, `BlockedDateRangeFactory`
- Playwright browser install in Docker image

### Unit & view tests — Accounts
- Registration form rejects duplicate email
- Registration form requires first name, last name
- Company account requires company name
- Passwords must match
- Inactive user cannot log in (email not verified)
- Email verification token activates account; expired/bad token is rejected
- `display_name` returns company name for company accounts, full name for person accounts
- `is_company` property returns correct value
- Profile view returns 200 for logged-in user
- Profile view redirects logged-out user to login
- Profile edit saves changes correctly
- Account deletion removes the user record and logs out the session
- Non-owner cannot access another user's profile edit

### Unit & view tests — Listings
- `Listing.cover_photo` returns first photo or None
- `Listing.get_absolute_url` returns correct URL
- `BlockedDateRangeForm` rejects end date before start date
- `ListingForm` requires auto-accept message when auto-accept is enabled
- Browse page returns 200 for logged-out user
- Browse page filters by keyword, category, location
- Inactive listings do not appear on browse page
- Listing detail returns 200 for logged-out user
- Listing detail shows login prompt instead of owner contact for logged-out user
- Listing detail shows owner contact for logged-in non-owner
- Listing detail shows owner management panel for owner
- Create listing requires login
- Create listing saves correctly with required fields only
- Create listing saves correctly with all optional fields
- Edit listing is restricted to owner (non-owner gets 404)
- Delete listing is restricted to owner (non-owner gets 404)
- Toggle active/inactive updates `is_active` flag
- My listings page shows all owner's listings (active and inactive)
- Photo delete removes the file and the record
- Blocked date add creates the record; delete removes it

### E2E tests — Accounts
- Register → receive verification email (console) → verify → log in → see profile
- Log in with wrong password shows error
- Log out redirects to home

### E2E tests — Listings
- Logged-in user creates a listing (fills required fields, uploads a photo) → listing appears on browse page
- Auto-accept message field is hidden by default, shown when checkbox is ticked
- Browse page: search by keyword returns matching listing; clear filters resets results
- Logged-out user visits listing detail → sees price, no owner contact details
- Owner deactivates listing → listing disappears from browse page
- Owner adds and removes a blocked date range on the detail page

---

## Phase 2: Bookings
*Covers [DEV.md Phase 4](DEV.md#phase-4-bookings)*

### Unit & view tests
- Availability conflict check: overlapping confirmed bookings block a new request
- Availability conflict check: non-overlapping requests are allowed
- Quantity check: bookings up to quantity limit are allowed; over limit is blocked
- Auto-accept: booking is confirmed immediately when listing has auto-accept enabled
- Auto-accept: predefined message is posted to the thread on auto-accept
- Booking status transitions: pending → confirmed, pending → rejected, confirmed → cancelled, confirmed → completed
- Price calculation for different duration types (day, weekend, week, month) including base fee
- Booking detail is visible to both owner and renter; hidden from others
- Renter cannot book their own listing
- Cancel action is available to both owner and renter on a confirmed booking

### E2E tests
- Renter submits a booking request → owner sees notification → owner confirms → renter sees confirmed status
- Auto-accept flow: request submitted → immediately confirmed → predefined message appears in thread
- Owner rejects a request → renter sees rejected status
- Either party cancels a confirmed booking

---

## Phase 3: Messaging
*Covers [DEV.md Phase 5](DEV.md#phase-5-messaging)*

### Unit & view tests
- Message thread is scoped to a booking (owner and renter can read/write; others cannot)
- Sending a message saves it and shows it in the thread
- Disclaimer text is present in the thread template

### E2E tests
- Owner and renter exchange messages within a booking thread
- Message appears immediately after submission

---

## Phase 4: Notifications
*Covers [DEV.md Phase 6](DEV.md#phase-6-notifications)*

### Unit & view tests
- Notification is created for each triggering event (new request, confirmed, rejected, cancelled, new message)
- Correct recipient is assigned for each event type
- Unread count reflects unread notifications
- Mark individual notification as read updates the read flag
- Mark all as read clears all unread for the user
- Notifications of other users are not accessible

### E2E tests
- Bell icon badge count increments when a new notification arrives
- Clicking a notification marks it as read and navigates to the related page
- "Mark all as read" clears the badge

---

## Phase 5: Administration + Static Pages
*Covers [DEV.md Phase 7](DEV.md#phase-7-administration) and [DEV.md Phase 8](DEV.md#phase-8-static-pages--legal)*

### Unit & view tests
- Non-staff user cannot access `/admin/`
- Staff user can access `/admin/`
- Deactivating a user (`is_active = False`) prevents login
- About, Help, Privacy Policy, Terms pages return 200 for logged-out users
- Account deletion flow removes all personal data fields

### E2E tests
- Admin deactivates a user → that user cannot log in
- Static pages render in both English and Finnish

---

## Phase 6: Translations
*Covers [DEV.md Phase 9](DEV.md#phase-9-translations)*

### Unit & view tests
- Language switcher sets the session language
- Key pages return 200 in Finnish locale

### E2E tests
- Switch language to Finnish → UI strings change to Finnish
- Switch back to English → UI strings revert
- User-generated content (listing title, description) is not translated

---

## Phase 7: Regression & pre-deployment
*Runs before [DEV.md Phase 11](DEV.md#phase-11-deployment)*

- Full pytest suite passes with zero failures
- E2E suite passes against the production Docker Compose stack (`docker-compose.prod.yml`) on a staging run
- No DEBUG-only code paths reachable in production settings
- Static files collected and served correctly by WhiteNoise / Nginx
