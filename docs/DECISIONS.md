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
