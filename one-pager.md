# FolioDesk
**Track:** Backend Development

**Stack:** Python, FastAPI, PostgreSQL (SQLite for tests), SQLAlchemy + Alembic, JWT auth

**Target user:** A solo freelance developer who maintains software for 10+ clients (primary user), and those clients (secondary users)

**Problem:** Client requests arrive across scattered channels with no record of urgency or effort, so the freelancer cannot tell what to do first. Clients have no visibility into progress, and the freelancer's public portfolio is kept separately and goes stale.

**Entities:** User, Client, Project, Request, InviteCode, Comment

**Core flow:**

Admin creates a client and issues an invite code **->** client registers and logs in **->** client submits a request on their own project **->** admin fetches the ranked queue (GET /dashboard/queue) **->** admin updates status and effort **->** client sees the new status

**In scope:**
- Admin and client roles with ownership checks (clients only ever see their own data)
- Invite-code registration plus email/password login with JWT
- CRUD for clients, projects and requests, with a validated status workflow
- Priority score from request type, client tier, waiting time, effort and admin pin
- Admin summary endpoints (open requests by status, project and client)
- Public portfolio endpoint showing only projects flagged public
Out of scope:
- Live uptime or health monitoring of client systems
- A frontend dashboard
- Payments and invoicing
- File uploads and attachments
- Email or real-time notifications, and multiple freelancers (multi-tenancy)

**Success looks like:**

Client A can never read or change Client B's data (proven by tests), the ranked queue is explainable by a documented rule, and someone else can run the API from the README.

Main entity for Week 1 CRUD: Request
Roles: admin (the freelancer, seeded), client (registered via invite code)
Auth model: Admin issues a single-use, expiring invite code per client. The client uses it once to register with email and password, then logs in normally.
Priority rule (summary): type (bug 40 / update 20 / feature 10) + client tier (0 / 15 / 30) + waiting time (2 per day, max 20) + quick-win bonus (10 for up to 2h, 5 for up to 8h) + pinned (+1000)
Key design decisions: Score computed at read time, not stored, because waiting time changes daily. Invite codes stored hashed. FastAPI validation errors mapped to 400 to match the guide.
Top 3 risks:
1. Scope creep into monitoring, a UI or notifications
2. An access-control bug that exposes one client's data to another
3. Priority weights that feel arbitrary