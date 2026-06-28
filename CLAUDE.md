# Vigil — Family Medical Readiness System

A readiness system: a family coordinator prepares calmly once, keeps it true over time,
and whoever is present in a medical crisis can act fast and correctly — without the patient
or coordinator needing to help in that moment.

This is a LEARNING PROTOTYPE, built strictly one slice at a time. Not production.

## Deeper context (read these when relevant — do not inline them here)
- Concept & principles:        docs/medical-readiness-design.md
- Prototype scope & build order: docs/prototype-spec.md
- Stack, schema, conventions:   docs/architecture.md
- Decisions log (READ before changing architecture): docs/DECISIONS.md

## Stack
- Backend: FastAPI (Python), SQLAlchemy 2.0, Pydantic v2, Alembic migrations
- DB: PostgreSQL (psycopg2)
- Crisis page: server-rendered (Jinja2 now; Next.js SSR in a later slice)
- Coordinator frontend: React (later slice; backend-first for now)

## Hard guardrails — YOU MUST follow these
- The crisis/script output path is DETERMINISTIC TEMPLATING ONLY. Never put an LLM in the
  crisis output path. (AI is permitted later for *ingestion* only, human-confirmed.)
- Fake data only. Never invent or assume real medical / insurance data.
- Secrets via environment variables only — never in code, never committed.
- Parameterized queries only (use the ORM / bound params). Validate all input via Pydantic.
- Keep the fact→sentence transform PURE and isolated in app/services/transform.py:
  no DB, no HTTP, no side effects. It is the conceptual heart.

## Conventions
- SQLAlchemy 2.0 style: Mapped[] + mapped_column(), relationship(back_populates=...).
- crisis_slug is generated server-side with secrets.token_urlsafe — never client-supplied,
  never sequential. The crisis route returns a bare 404 on miss (no info leak).
- Child collections (medical_facts, emergency_contacts) are first-class resources with stable
  UUIDs, edited via granular per-item POST/PATCH/DELETE — NOT full-replace. See decision D5.
- At least one test per slice. Transform logic is unit-tested with no DB session.

## Workflow — IMPORTANT
- Build STRICTLY one slice at a time, in the order in docs/prototype-spec.md.
  Do NOT add anything outside the current slice. If something seems needed sooner, STOP and ask.
- Before significant code, propose the file structure + any schema changes and wait for approval.
- Explain the "why," and flag any decision with long-term architecture impact.
- If unsure about a library version or current best practice, say so — do not guess.

## Run & test (from backend/)
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env            # set DATABASE_URL (Postgres must be running)
    alembic upgrade head
    python seed.py                  # loads fake data
    uvicorn app.main:app --reload   # crisis page at /c/{slug}
    pytest                          # run tests

## Status
- Slice 1 (walking skeleton — crisis page renders facts as a script): DONE
- Slice 2 (steadying opener + ordered pre-composed sentences): DONE (absorbed into slice 1)
- Slice 3 (coordinator write API — person, facts, contacts): DONE
  - Endpoints: POST/GET/PATCH persons; POST/PATCH/DELETE facts; POST/PATCH/DELETE contacts
  - Granular identity-preserving edits (D5); slug generation centralized
  - 16 tests + all existing tests passing; no schema migrations needed
- Slice 4 (second family member — list view + per-person crisis URLs): DONE
- Slice 5 (logistics field + guard-rail line): DONE
  - New `insurance` table (one-to-one per person; migration 0002); D7 logged
  - Endpoints: PUT-upsert / PATCH / GET /coordinator/persons/{id}/insurance
  - transform.py composes a deterministic money guard-rail (cashless → "don't pay
    upfront"; otherwise "keep every bill"); rendered as crisis script Step 3
  - 47 tests passing (was 30); seed gives both members an insurance row
- Slice 6 (QR code per person from the crisis URL): DONE
  - `qrcode` dep (SVG, no Pillow); isolated app/services/qr.py
  - Endpoints: GET /coordinator/persons/{id}/qr.svg (image) + /qr (printable card)
  - `base_url` config setting builds {base_url}/c/{slug}; crisis_url() centralized
  - Roster links to each card; 54 tests passing (was 47); no schema change
- Slice 7 ("Notify family" button — simulated send + location + secure link): DONE
  - New `notification_event` table (migration 0003); D8 logged
  - Public endpoint POST /c/{slug}/notify; pure services/notify.py message builder
  - Crisis page button → browser geolocation → AJAX → per-contact message preview
  - Location optional (graceful when denied); secure link = crisis URL until Slice 9
  - 68 tests passing (was 54)
- Slice 8 (per-fact "last confirmed [date]" freshness signal): DONE
  - `medical_fact.last_confirmed_at` (migration 0004); D9 logged
  - transform now pure-with-`now`: doctor_lines are DoctorLine(text/label/is_stale);
    humanize_age + STALE_AFTER_DAYS=180 in transform.py
  - Bumped on create, on /confirm endpoint, and on value/type edit (edit = re-affirm)
  - Crisis page shows "confirmed X ago"; stale (>180d) flagged amber "may be outdated"
  - Seed backdates 2 facts for a fresh/stale demo mix; 85 tests passing (was 68)
- NEXT → Slice 9: two-level hint (open script vs. richer "for family" view)
