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
