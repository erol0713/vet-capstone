# Bayawan Dog Pound & Veterinary Office System

Web-based system for Bayawan City Veterinary Office. Public pages are view-only;
all actions require authentication + verification.

## Stack
- Django 4.2+ (local uses Django 5)
- SQLite (dev), PostgreSQL (prod)
- Bootstrap 5.3, Bootstrap Icons, Chart.js, face-api.js
- Pillow (image uploads)
- pytest for tests (80% minimum coverage target)

## Quick Start (Dev)
1. Create a virtualenv and install dependencies.
2. Run migrations.
3. Create a superuser.
4. Start the server.

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Notes
- Custom user model is in `users.CustomUser` (do not remove).
- Media files stored in `media/`.
- Static assets in `static/`.
- API endpoint: `POST /api/reports` accepts JSON payload with `location_method` and returns `report_id`.
- Set `GOOGLE_MAPS_API_KEY` in the environment to enable map search and pin drop on the report form.
- Keep files under 500 lines; split into modules as needed.
- Penalty checklist includes a printable citation ticket with owner + violations.
- Reclaim requests require an ownership proof upload for admin/staff review.
- Adoption reservations for captured dogs notify after 3 days if unclaimed; users confirm, staff schedule appointments.
- Staff can record completed dog vaccinations (vaccination date + expiration) or proof-confirmed expiration-only entries.
- Run `python manage.py send_vaccine_notifications` regularly to send 3-day expiry reminders and expired vaccine prompts.
- Owner-registered dogs are hidden from `My Dogs` until admin/staff approves vaccination compliance.

## Design System
- Base CSS files:
  - `static/css/theme.css` (tokens, typography, Bootstrap variable overrides)
  - `static/css/utilities.css` (reusable utility classes for spacing, clusters, filters, badges, and mobile table stack)
  - `static/css/components.css` (shared components: cards, chips, tables, status pills, steppers)
  - `static/css/layout.css` (page layout, hero, section spacing, mobile bottom nav)
- Page-level overrides live in `static/css/pages/` (analytics, profile, reports, dogs, penalties, notifications, auth).
- `templates/base.html` loads the base CSS files; each page opts into its page CSS via `{% block extra_css %}`.
- Palette rule: white-dominant surfaces, warm yellow highlights, green primary actions.

## MVP User Flows (Draft)
- Public browsing: view dog pound inventory and public reports (read-only).
- Public report: submit stray report with map/manual address + media upload.
- Verified owner: register dog, submit adoption request, submit reclaim request.
- Staff/Admin: intake management, report triage, adoption/reclaim approvals, penalty processing, vaccination scheduling, analytics review.
