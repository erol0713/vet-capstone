# System Gaps (as of Feb 10, 2026)

This list is based on a quick repo scan plus `TASK.md`. It may not cover in‑progress work.

**Product/Workflow**
- Email OTP delivery is dev-only (OTP code shown in `users/views.py`).
- Face liveness is a stub (server only checks `liveness_passed` in `users/views.py`).
- Strike enforcement is not implemented (profile has `offense_count` and `status_badge` in `users/models.py`, no update logic found).
- 72‑hour intake auto‑status updates require a scheduler (command `process_reclaim_window` added, but no cron/Task Scheduler/Celery).
- SMS/email notification channels are not integrated (no Twilio/SMTP code found).
- Barangay GIS mapping is not implemented (no mapping module beyond report map UI).
- Vaccine notifications command exists, but there is no job scheduler to run it.

**Analytics**
- Adoption vs reclaim trend is not time‑series; only totals are computed in `analytics/views.py`.
- Kennel utilization analytics not found.
- Compliance trend analytics not found.

**Testing/Delivery**
- No CI pipeline or coverage gate found (no `.github/workflows`).
- No deployment container config found (`Dockerfile` / `docker-compose` missing).
- 80% coverage target is not enforced by tooling.
    
