# Decisions Log — Vigil

Short records of architectural decisions and *why*. Append as you go; don't rewrite history.
Each entry: what was decided, the reasoning, and what it affects downstream.
This file exists so a fresh session inherits the reasoning, not just the rules.

## D1 — Database: PostgreSQL (not MongoDB)
The data is relational (family → members → facts/contacts/insurance, plus access tokens and
an audit log). We want integrity constraints and a clean access-control story.
**Affects:** schema design; the later tiered-access + audit slices.

## D2 — Backend: FastAPI (not Node/Express/Nest)
The one differentiating feature — LLM/vision document extraction — is native to Python and
reuses prior RAG work; Pydantic gives typed validation cheaply. Frontend stays JS (React/Next),
so the project ends up polyglot, mirroring real AI-product teams.
**Affects:** language for all backend slices; extraction lives here later.

## D3 — AI placement: ingestion only, never crisis output
Calm mode may later use an LLM to extract facts from an uploaded document FOR COORDINATOR
CONFIRMATION (human-in-the-loop). The crisis script is deterministic templating only — no
model in the safety-critical path, ever. ("AI where a human catches errors; deterministic
where a vulnerable person doesn't.")
**Affects:** transform.py stays deterministic; extraction.py (later) is the only AI surface.

## D4 — crisis_slug: server-generated, unguessable, permanent
Generated with secrets.token_urlsafe, unique, never client-supplied, never sequential. The
crisis route returns a bare 404 on miss so it leaks nothing about the slug space. Treated as
permanent once a QR is printed (slice 6).
**Affects:** the person-creation path; the later QR + access-log slices.

## D5 — Child collections are identity-preserving resources (granular edits, not full-replace)
medical_facts and emergency_contacts are edited via per-item POST/PATCH/DELETE endpoints,
each row keeping a stable UUID — NOT delete-all-and-recreate on save.
**Why:** in a later slice (8) each fact carries its own `last_confirmed_at`. Full-replace would
reset every fact's identity and timestamp on every edit, destroying the "confirmed 8 months ago"
freshness signal — which is a core concept. Confidence metadata requires stable identity.
**Trade-off:** a form save becomes several calls (chattier). That's a frontend concern, solvable
later with a batch endpoint; the backend resource model respects identity now.
**Affects:** slice 3 endpoint design; slice 8 (confidence timestamps).

## D6 — Family roster lives on the coordinator surface, not public crisis
The family roster (listing all persons with their crisis_slugs) is served from
`GET /coordinator/persons`, not from a public `/` route.
**Why:** D4 treats the crisis_slug as an unguessable capability; publishing all slugs at a
public endpoint undermines that. Listing all family members is a coordinator setup activity
(calm mode), separate from the public crisis surface (/c/{slug}). This mirrors the prototype's
foundational "two surfaces" separation (prototype-spec.md:21).
**In the prototype:** both surfaces are local-only and unauthenticated (no real auth yet).
The separation is architectural, not enforced, and makes room for real auth + tiering later.
**Affects:** API surface (coordinator is `/coordinator/*`); later slice when real auth arrives.

## D7 — Insurance is one-to-one with a person; edited via PUT-upsert + PATCH (not the D5 collection pattern)
The insurance row is a single logistics record per person (`relationship(uselist=False)`,
unique FK on `insurance.person_id`). It is NOT a granular collection like medical_facts /
emergency_contacts, so D5's per-item POST/PATCH/DELETE does not apply.
**Endpoints:** `PUT /coordinator/persons/{id}/insurance` create-or-replaces the single row;
`PATCH` does a partial update; `GET` reads it (404 when none on file).
**Why:** a singleton resource maps cleanly to PUT (idempotent upsert) — adding a collection-style
POST would imply multiple insurance rows, which the unique constraint forbids. The PUT path is
identity-preserving on update (it mutates the existing row rather than delete+recreate), so a
future per-record `last_confirmed_at` (slice 8) survives — consistent with the *spirit* of D5
even though the endpoint shape differs.
**Crisis surface:** the row becomes a deterministic "money guard-rail" in transform.py — the
`cashless` flag chooses "don't pay upfront" vs. "keep every bill for reimbursement." No LLM
in this path (D3). Rendered as a third script step, after the clinical "tell the doctor" lines.
**Affects:** slice 5 schema + endpoints; slice 8 (confidence timestamps); the transform's growth.

## D8 — "Notify family" is a public-crisis-surface action; send is simulated; secure link = crisis URL (for now)
The notify trigger is `POST /c/{slug}/notify` on the public crisis router, NOT under
`/coordinator/*`. The responder in the room triggers it, so it belongs with the responder-facing
surface; the unguessable slug is the only gate, same as the page itself (consistent with D6's
two-surface split and D4's slug-as-capability).
**Simulated send:** no real SMS/WhatsApp. We persist one `notification_event` audit row per tap
(`status="sent"`, location nullable) and return the messages that *would* be dispatched per
contact. Message composition is a PURE function (services/notify.py), mirroring transform.py —
"data becomes words" stays deterministic and unit-testable with no DB.
**Location is optional:** the browser geolocation prompt can be denied/time out; the POST still
succeeds with null coordinates and the message degrades to "Location: not shared." The flow
never blocks on permission.
**Secure link:** the message's "Details:" link is the crisis URL (`{base_url}/c/{slug}`) for now.
The richer, tiered "for family" view is Slice 9; until it exists, pointing at the crisis page is
the honest target rather than inventing a dead link.
**Affects:** slice 7 schema/endpoint/template; slice 9 (the secure link gains a family-tier view);
later slices for real SMS, rate-limiting, delivery-ack, and escalation.
