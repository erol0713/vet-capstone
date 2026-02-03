AGENTS.md
=========

Purpose
-------
This file defines project-specific instructions for AI agents working in this
repository. Follow these rules unless the user explicitly overrides them.

Project Context
---------------
Dog Pound & Veterinary Office Management System for Bayawan City.
Web-based, public read-only access with authenticated + verified actions.
Primary stack:
- Backend: Django 4.2+, Python, PostgreSQL (prod), SQLite (dev)
- Frontend: Bootstrap 5.3, Bootstrap Icons, Chart.js, face-api.js
- Testing: pytest (min 80% coverage)

Core Modules
------------
1) User Management: Gmail OTP, roles (Admin/Staff/User), face verification,
   legal consent, profile/ownership, strike count + status badge.
2) Dog Pound & Stray Ops: intake, inventory lifecycle, kennel occupancy,
   GPS/barangay tagging, public browsing, auto status update after 72 hours.
3) Adoption & Reclaim: reservations, requests, staff verification, approvals,
   reclaim date recording, status-based restrictions.
4) Penalty Management: ordinance checklist, JS fee computation, redemption +
   lodging day computation, strike enforcement, finalization + lock.
5) Vaccination & Health: records, expiration monitoring, reminders, analytics,
   strike integration.
6) Notifications: bell + unread count, vaccine alerts, strike warnings, updates,
   announcements.
7) Analytics/Reporting: monthly capture stats, barangay hotspots, revenue by
   ordinance section, compliance trends, adoption vs reclaim, kennel utilization.

Workflow
--------
- Define/confirm feature in TASK.md before implementing.
- Implement backend logic first, then templates + CSS.
- Add tests (success, edge, failure cases) per feature.
- Update documentation (README.md + inline comments for complex logic).

Non-Negotiable Constraints
--------------------------
- Mobile-first and touch-friendly UI.
- Max file length: 500 lines (split into modules if needed).
- Page load under 3 seconds.
- Django security best practices (CSRF, auth, permissions, data validation).
- Verification gating for all protected actions (Admin/Staff may bypass).

Conventions
-----------
- Use role-based decorators/mixins consistently.
- Track strikes and status badges (green/orange/red) on profiles.
- Use consistent status enums for Dog and Report lifecycles.
- Ensure penalties are computed deterministically and locked after finalization.
- Notifications should be queued and visible in UI with unread counts.
- Analytics queries must be efficient and scoped by date range.

Testing Guidance
----------------
- Use pytest; mirror app structure in tests.
- Each feature includes: success, edge, failure.
- Add integration tests for auth, role enforcement, verification, strike logic,
  and penalty computations.

UX/Design Guidance
------------------
- Bootstrap 5.3 + custom CSS system.
- Card-based layout, sticky top nav, mobile bottom nav (user portal).
- Accordion penalty checklist, sticky penalty total bar.
- Full-screen mobile notification panel, print-optimized citation ticket.

When in Doubt
-------------
- Ask for clarification only if requirements block progress.
- Prefer smaller, composable files to respect line limits.
- Do not add new dependencies without updating docs and tests.
