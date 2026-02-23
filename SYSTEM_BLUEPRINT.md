# Bayawan Vet Office System - Full Blueprint

## 1) System Overview

Bayawan Vet Office System is a web-based civic operations platform for:

- Public dog pound transparency and stray reporting
- Authenticated owner services (registration, requests, profile/compliance)
- Staff/admin operations (intake, approvals, penalties, verification, analytics)
- Notification-driven workflows and accountability

Primary goals:

- Improve dog capture-to-resolution lifecycle tracking
- Digitize adoption/reclaim and penalty operations
- Enforce account verification for protected user actions
- Surface operational insights through analytics

## 2) Technical Architecture

### Backend

- Framework: Django 4.2+
- Language: Python
- Database:
  - Dev: SQLite
  - Prod: PostgreSQL

### Frontend

- Django Templates
- Bootstrap 5.3 + Bootstrap Icons
- Custom CSS system (`theme.css`, `components.css`, `layout.css`, `styles.css`)
- Vanilla JS for UI behaviors
- Chart.js for analytics charts
- face-api.js scaffold for face/liveness flow

### Testing

- pytest with project target: at least 80% coverage

## 3) App Modules (Bounded Contexts)

### `core`

- Home page and shared infrastructure
- `TimeStampedModel` base class
- Operational management commands

### `users`

- Custom auth model (`CustomUser`)
- Roles: `ADMIN`, `STAFF`, `OWNER`
- OTP verification, account verification, face verification
- Profile and compliance metadata
- Admin/staff user management actions

### `dogs`

- Dog intake and inventory lifecycle
- Public listing/detail
- Registered dogs and owner linkage
- Vaccination request queue integration

### `reports`

- Public stray reporting form/list
- API endpoint for report intake
- Staff report queue/detail/status updates

### `adoption`

- Adoption reservation workflow
- Reclaim request workflow
- Staff scheduling and status transitions

### `penalties`

- Ordinance checklist
- Deterministic fee computation and line items
- Finalization lock and printable receipt

### `vaccinations`

- Vaccination record lifecycle
- Expiry reminder scheduling hooks

### `notifications`

- In-app notifications
- Bell unread count + inbox + mark read/read all

### `analytics`

- Daily metrics collection
- Staff analytics dashboard with date-range filtering

## 4) Role Model and Access Rules

### Guest (Public)

- Access: home, dog pound list/detail, public reports, auth pages
- No protected write actions

### Owner/User

- Access: dashboard, profile, dog registration, requests, notifications
- Protected owner actions require:
  - `email_verified = true`
  - `is_verified = true` (identity/face verification gate)

### Staff/Admin

- Access: analytics, queues, dog operations, penalties, verifications
- Verification gate bypassed for operations role

## 5) Core Data Blueprint

### Users and Identity

- `CustomUser`
  - auth identity
  - role
  - verification flags
  - legal consent
- `UserProfile`
  - personal/contact fields
  - offense count
  - status badge (`GREEN`, `ORANGE`, `RED`)
- `EmailOTP`
  - hashed code, expiry, purpose
- `FaceVerification`
  - status (`PENDING`, `APPROVED`, `REJECTED`)
  - review metadata

### Dogs

- `Dog`
  - lifecycle status:
    - `IMPOUNDED`
    - `AVAILABLE`
    - `ADOPTED`
    - `RECLAIMED`
    - `RELEASED`
  - intake metadata
  - owner link
  - barangay/location
  - vaccination fields

### Reports

- `Report`
  - report type/status enums
  - map/manual location data
  - reporter contact
  - media proof

### Requests

- `AdoptionReservation`
  - status:
    - `PENDING`
    - `APPROVED`
    - `REJECTED`
    - `CANCELLED`
    - `COMPLETED`
  - scheduling/confirmation fields
- `ReclaimRequest`
  - status:
    - `PENDING`
    - `APPROVED`
    - `REJECTED`
    - `COMPLETED`
  - ownership proof

### Penalties

- `PenaltyCase`
  - owner + dog context
  - computed totals
  - finalized lock metadata
- `PenaltyLineItem`
  - itemized computed charges
- `PenaltyChecklistItem`
  - ordinance sections:
    - `SECTION_28`
    - `SECTION_29`
    - `ADDITIONAL`

### Notifications and Analytics

- `Notification`
  - per-user message
  - read state
  - optional action URL
- `DailyMetric`
  - `date`, `metric`, `value`
  - unique by date + metric key

## 6) Lifecycle Workflows

### A) Registration + Verification

1. User registers
2. OTP verification (email)
3. Login
4. Profile completion
5. Face verification submission
6. Staff/admin review
7. Approved users can perform protected owner actions

### B) Public Report to Resolution

1. Public report submitted (form/API)
2. Report enters staff queue
3. Staff reviews and updates status
4. Notifications sent to relevant parties

### C) Dog Intake to Outcome

1. Staff creates intake record
2. Dog remains impounded during reclaim window
3. Auto-process command checks window expiry
4. Dog transitions to `AVAILABLE` if not reclaimed
5. Final outcomes: adopted/reclaimed/released

### D) Adoption Workflow

1. Owner submits adoption reservation (or direct adoption where allowed)
2. Staff queue review and schedule
3. Staff approves/rejects/cancels/completes
4. Dog status and ownership updates are persisted

### E) Reclaim Workflow

1. Owner submits reclaim request with proof
2. Staff verifies and processes
3. Reclaim completion updates dog owner/status
4. Related penalties and reclaim date are recorded

### F) Penalty Workflow

1. Staff selects ordinance checklist items
2. System computes deterministic totals
3. Lodging/redemption conditions applied
4. Case finalized and locked from further edits
5. Printable receipt generated

### G) Vaccination Reminder Workflow

1. Vaccination records tracked
2. Scheduled command generates reminder/expiry notifications
3. Notifications displayed in bell + inbox

## 7) URL and IA Blueprint

### Public IA

- Home (`/`)
- Dog pound list/detail
- Public reports (list + form)

### Owner IA

- Dashboard
- Profile/edit
- Register/manage owned dogs
- My requests (adoption/reclaim)
- Verification status pages
- Notifications

### Staff/Admin IA

- Analytics dashboard
- Manage dogs (intake/inventory/by owner)
- Vaccination request queue
- Reports queue/detail
- Adoption/reclaim queue/detail/scheduling
- Penalties checklist/receipt
- User verification and management

## 8) Frontend System Blueprint

### Layout and Navigation

- Shared layout in `base.html`
- Role-aware top navbar
- Notification bell dropdown with unread counter
- Owner mobile bottom nav for quick actions

### UI Language

- Warm civic green palette
- Elevated white cards
- Compact spacing
- Status pills and chips
- Filter bars and queue tables/cards
- Accessible focus and touch-friendly controls

### CSS Structure

- `static/css/theme.css` (tokens, base types, colors, spacing)
- `static/css/components.css` (cards, pills, forms, tables, alerts, states)
- `static/css/layout.css` (shell, navbar, responsive layout)
- `static/css/styles.css` (global utility and behavior refinements)

### JavaScript Structure

- `static/js/navbar.js`:
  - mobile menu toggle
  - active nav highlight
  - sticky shadow on scroll
  - dropdown behavior
- Feature scripts:
  - analytics rendering
  - penalty computation UI
  - report form map/media logic
  - face liveness scaffolding

## 9) Security Blueprint

- CSRF protection for mutating requests
- Django auth/permission checks per view
- Role decorators/mixins consistently applied
- Verification gate for owner protected actions
- Safe redirect validation for notification action URLs
- Data validation in forms and API endpoints

## 10) Automation and Operations

### Management Commands

- `process_reclaim_window`
  - transitions eligible dogs to available
  - updates lodging penalties
  - triggers related notifications
- `send_vaccine_notifications`
  - sends pre-expiry and expiry alerts
- `fix_intake_visibility`
  - normalizes intake state visibility
- `seed_data`
  - loads demo/test fixtures

## 11) Analytics Blueprint

Key dashboards should track:

- Monthly dog captures
- Barangay hotspots
- Adoption vs reclaim trends
- Penalty revenue by section
- Compliance status trends
- Kennel utilization

Design:

- Query scoped by date range
- Aggregation by lightweight metric keys
- Chart.js visualizations fed by server-side data

## 12) Testing Blueprint

Each feature should include:

- Success case
- Edge case
- Failure case

Critical integration tests:

- OTP + auth flow
- Role enforcement and verification gating
- Adoption/reclaim transitions
- Penalty computations and finalization lock
- Notifications unread/read mechanics
- Analytics date-range query correctness

## 13) Performance and Quality Constraints

- Mobile-first responsive UX
- Touch-safe controls
- No horizontal overflow on small screens
- File size target: split files before >500 lines
- Keep page load under 3 seconds where feasible
- Reuse components and avoid CSS duplication

## 14) Recommended Future Enhancements

- Full production liveness anti-spoof flow
- GIS map visualization for hotspots
- Message provider integration (SMS/email)
- Analytics query optimization and caching
- Audit logs for administrative actions

