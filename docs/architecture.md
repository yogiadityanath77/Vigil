# Architecture — Family Medical Readiness System
*(companion to `medical-readiness-design.md` and `prototype-spec.md` — the "how")*

## Decided stack (and why)
- **Backend: FastAPI (Python).** Chosen because the one differentiating feature — LLM/vision extraction of documents into structured facts — is native to Python and reuses prior FastAPI + RAG work, and Pydantic gives typed/validated models cheaply (system-design discipline). FastAPI is also the rising standard for serving AI in production.
- **Database: PostgreSQL.** The data is relational (family → members → facts/contacts/insurance, plus access tokens and an audit log). Postgres gives integrity constraints and a clean access-control story — a direct level-up of prior RBAC work. *Be ready to explain this choice over MongoDB.*
- **Frontend: React, with the crisis page server-rendered (Next.js).** The coordinator app is a normal SPA; the crisis page must load instantly for a stranger on weak signal, so it's SSR/static — a deliberate performance choice, not SPA-by-default.
- **Later (justified by need):** Redis for rate-limiting the notify trigger + token/session storage; WebSockets (Socket.io) for alert acknowledgment and escalation.
- **ORM/validation:** SQLAlchemy + Pydantic. **QR:** `qrcode`. **Location:** browser Geolocation API.

## The non-negotiable AI-placement rule
- **AI is for ingestion, never for crisis output.** In *calm mode*, an LLM/vision pipeline may extract facts from an uploaded prescription/discharge summary into the form **for the coordinator to confirm** (human-in-the-loop). In *crisis mode*, the script is **deterministic templating only** — no model in the safety-critical path, ever. This boundary (AI where a human catches errors; deterministic where a vulnerable person doesn't) is a core design decision, not a preference.

## Folder structure (backend, starting point)
```
backend/
  app/
    main.py            # FastAPI app + router registration
    db.py              # engine/session
    models/            # SQLAlchemy models
    schemas/           # Pydantic schemas
    routers/           # coordinator routes, public crisis routes
    services/
      transform.py     # fact -> sentence transform (the conceptual heart; keep isolated)
      extraction.py    # (later) LLM/vision document extraction
    templates/         # (if crisis page is SSR from backend in early slices)
  tests/
  .env.example
frontend/              # React / Next.js (added when the slice needs it)
```

## Data model (prototype-level, Postgres)
Start normalized — it teaches the relational design and supports the access/audit story. (You *could* start medical facts as columns and normalize later; the table version below is the better learning target.)

- **person**: `id (uuid)`, `full_name`, `date_of_birth`, `blood_group`, `crisis_slug (unguessable, unique)`, `last_confirmed_at`, `created_at`
- **medical_fact**: `id`, `person_id (fk)`, `type` (`allergy` | `medication` | `condition`), `value`, `last_confirmed_at`
- **emergency_contact**: `id`, `person_id (fk)`, `name`, `phone`, `relationship`, `notify_order`
- **insurance**: `id`, `person_id (fk)`, `provider`, `policy_number`, `hospital_preference`, `cashless (bool)`  — the logistics tier
- **access_token**: `id`, `person_id (fk)`, `token`, `tier` (`public` | `family`), `status` (`active` | `revoked`), `created_at`  — *real gating is a later slice; for the prototype the unguessable slug is enough, but model the table now*
- **access_log**: `id`, `token_id (fk)`, `scanned_at`, `ip`, `user_agent`  — *minimal/optional in the prototype*
- **notification_event**: `id`, `person_id (fk)`, `triggered_at`, `location_lat`, `location_lng`, `status`  — *for the simulated "Notify family" action*

Relationships: a person has many medical_facts, emergency_contacts, access_tokens; one insurance row; many access_logs (via tokens) and notification_events.

## Coding conventions & guardrails
- **Security:** parameterized queries only; secrets in env vars (`.env`, never committed); validate all input via Pydantic; treat the crisis route as public and expose only the open tier.
- **AI boundary:** see the non-negotiable rule above.
- **Data:** fake data only in a learning prototype — no real medical/insurance records until real auth + gating exist.
- **Structure:** keep `transform.py` isolated and pure (facts in → sentences out); it's the piece everything else grows around.
- **Process:** one slice at a time; propose structure/schema before big code; runnable code + one test per slice; explain tradeoffs and flag long-term implications.

## How this maps to the build
Follow the 10-step build order in `prototype-spec.md`. The crisis script transform and the Postgres schema above are introduced in Slice 1 (minimal subset), and the schema grows one slice at a time. The AI extraction pipeline (`extraction.py`) is the post-core "career slice," added only after the concept-conveying prototype runs.

*Living document — update it as decisions change, and mirror key decisions into `DECISIONS.md`.*
