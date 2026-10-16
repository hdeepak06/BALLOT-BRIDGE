# BallotBridge — Secure E-Voting Platform

> **"Your Voice. Your Choice. Your Future."**

**BallotBridge** is a modern, full-stack digital e-voting platform built with **Python Django, SQLite, Vanilla HTML5, CSS3, and JavaScript**. Engineered with digital governance best practices, BallotBridge models a double-blind secret balloting architecture, atomic database constraints, server-side eligibility validation, and certified results visualization with Chart.js.

---

## 🏛️ Platform Highlights & Architectural Features

### 1. Double-Blind Secret Ballot Architecture
- **Complete Identity Separation:** Cast votes are recorded in the `Ballot` table referencing only the `election` and `candidate` with an anonymized SHA-256 hash. **No foreign key to the `User` exists on the ballot record.**
- **Participation Ledger:** Turnout is tracked separately in the `VoterParticipation` ledger (`user_id`, `election_id`, `receipt_token`) to enforce one-person-one-vote without storing the candidate selection.
- **Voter Privacy Guarantee:** Neither system administrators, candidates, nor fellow voters can inspect which candidate a voter selected.

### 2. Strict One-Vote Enforcement & Race Condition Safety
- Every voting request is wrapped in a `transaction.atomic()` database block.
- A database-level `unique_together = ('user', 'election')` constraint prevents race conditions, replay attacks, or duplicate submissions.
- Once cast, ballots cannot be modified, deleted, or re-voted through application routes.

### 3. Server-Side Election Lifecycle Validation
- Validates the election status and voting window (`start_time <= now <= end_time`) on the server for every voting request. Client-side timers and form controls are strictly treated as advisory.
- Validates candidate-election relationship integrity on the server.
- Supports five distinct election lifecycle stages:
  $$\text{Draft} \longrightarrow \text{Scheduled} \longrightarrow \text{Active (Voting Open)} \longrightarrow \text{Closed} \longrightarrow \text{Results Published}$$

### 4. Certified Results & Chart.js Analytics
- Results remain **strictly locked and hidden** until voting closes and an authorized administrator officially publishes the tally.
- Visualized with responsive **Chart.js Bar and Doughnut charts** displaying verified vote counts, vote share percentages, and total turnout.
- Transparently announces plurality winners or declares official ties when top candidates receive equal tallies.

### 5. Verifiable Participation Receipts & Audit Ledger
- Voters receive a unique cryptographic receipt token (e.g. `BB-REC-4B11-9A02-...`) to independently verify their presence in the certified turnout roll.
- System actions (election creation, status transitions, candidate updates, publication) are captured in a tamper-evident, read-only `AuditLog`.

### 6. Academic & Portfolio Simulation Disclosure
- Clearly explains within the UI that ordinary application-level web controls do not establish the End-to-End Verifiability (E2EV), coercion resistance (e.g. JCJ protocols), or hardware security isolation required for statutory public parliamentary elections.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.12, Django 5.1
- **Database:** SQLite (development)
- **Frontend:** Vanilla HTML5, Semantic CSS3 Design System, Vanilla JavaScript (No React, No Tailwind)
- **Visual Analytics:** Chart.js 4 (via CDN)
- **Typography:** Google Fonts (*Plus Jakarta Sans*, *Outfit*, *JetBrains Mono*)
- **Icons:** Font Awesome 6
- **Branding:** Custom SVG Ballot Box Logo and Favicon

---

## 👥 Pre-Configured Demo Accounts

For instant evaluation, the platform includes a **One-Click Demo Switcher** on the homepage and login screens:

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **Election Administrator** | `admin` | `admin12345` | Full access to Admin Portal, create/edit elections, manage candidates, change statuses, view audit logs, publish results. |
| **Voter (Ready to Vote)** | `voter_alex` | `voter12345` | Alex Morgan (`BB-2026-78421`). Verified voter ready to cast a ballot in active elections. |
| **Voter (Pre-Voted Demo)** | `voter_priya` | `voter12345` | Priya Sharma (`BB-2026-89104`). Demonstrates the "Already Voted" state and receipt view. |
| **New Voter Profile** | `voter_david` | `voter12345` | David Chen (`BB-2026-64112`). Clean profile ready for testing. |

---

## 🚀 Getting Started

### 1. Clone & Enter Directory
```bash
cd g:/websites/medico
```

### 2. Apply Migrations
```bash
python manage.py migrate
```

### 3. Seed Demonstration Elections & Users
```bash
python manage.py seed_data
```

### 4. Run the Test Suite
```bash
python manage.py test
```
*Executes unit and integration tests verifying one-vote database constraints, active window checks, secret ballot decoupling, and results locking.*

### 5. Start the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your web browser.

---

## 🧭 Application URL Map

| Route | Description |
| :--- | :--- |
| `/` | Landing page featuring hero, metrics, how it works, active demos, and FAQ |
| `/dashboard/` | Responsive voter dashboard with tabs (Active, Scheduled, Results) and sidebar |
| `/election/<slug>/` | Election overview, timeline, candidate cards, and eligibility checker |
| `/election/<slug>/compare/` | Impartial side-by-side candidate manifesto & proposal comparison |
| `/election/<slug>/vote/` | Step 1 of voting: Candidate selection cards |
| `/election/<slug>/confirm/` | Step 2 of voting: Explicit review and irreversible warning |
| `/election/<slug>/receipt/<token>/` | Step 3 of voting: Verifiable cryptographic participation receipt |
| `/election/<slug>/results/` | Certified results dashboard with interactive Chart.js charts |
| `/admin-portal/` | Election Commission administrator dashboard & lifecycle management |
| `/admin-portal/audit-logs/` | Tamper-evident system and governance audit ledger |
| `/profile/` | Voter profile, verified digital ID card, and confidential voting ledger |
| `/security-disclaimer/` | Architectural analysis comparing web simulation to public E2EV systems |
| `/about/`, `/privacy/`, `/terms/` | Informational and governance policy pages |

---

## 🔒 Security Architecture Summary

```
                      +-----------------------------+
                      |   Authenticated Voter       |
                      |   (Django Session / Auth)   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Server-Side Validation    |
                      |   - Election is ACTIVE now? |
                      |   - Voter is ELIGIBLE?      |
                      |   - Already participated?   |
                      +--------------+--------------+
                                     |
                          [transaction.atomic()]
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 v                                       v
   +---------------------------+           +---------------------------+
   |        ANONYMOUS          |           |        TURNOUT            |
   |          BALLOT           |           |      PARTICIPATION        |
   |                           |           |                           |
   | - election_id             |           | - user_id                 |
   | - candidate_id            |           | - election_id             |
   | - ballot_hash (SHA-256)   |           | - receipt_token           |
   |                           |           |                           |
   | * NO USER FOREIGN KEY!    |           | * NO CANDIDATE LINK!      |
   +---------------------------+           +---------------------------+
                 |                                       |
                 v                                       v
   +---------------------------+           +---------------------------+
   | Certified Results Engine  |           | Voter Participation       |
   | (Chart.js Bar & Doughnut) |           | Verification Receipt      |
   +---------------------------+           +---------------------------+
```
