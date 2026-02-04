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
- Keep files under 500 lines; split into modules as needed.
- Penalty checklist includes a printable citation ticket with owner + violations.
