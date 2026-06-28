# Family Medical Readiness System — Design Concept & Build Plan
*(working title — a living document)*

## How to read this doc
The top sections (Problem, Concept, Key Decisions) are **settled** — they're the thinking that genuinely belongs upfront, and we've earned them through discussion. The bottom sections (System Shape, Process, First Slice) are **meant to evolve** as you build. Don't treat this as a fixed spec to complete before coding. Treat it as a map you edit as you learn. Edit freely.

---

## 1. The problem
In a medical emergency, families lose time and make worse decisions not mainly because of money, but because of **confusion under stress**. The information needed to act — medical facts, who to call, insurance/logistics — is scattered, lives in one person's head or phone, and isn't reachable by whoever happens to be in the room.

The real gap (the part existing tools *don't* cover):
- Phone Medical ID solves one person, basics only, on one device.
- Nobody covers the **family-level**, **logistics-aware** (insurance, cashless, empanelment), **kept-fresh** layer that reaches **whoever is present**.

Three different people, who are not the same person:
- **Coordinator** — the organized, slightly anxious family member who sets this up and maintains it. *This is the real user.* (For this project: you.)
- **Responder** — whoever is in the room during the crisis. The beneficiary. Often panicking, often not the coordinator.
- **Patient** — the subject of the data, almost never the user, possibly unconscious.

## 2. The concept
This is a **readiness system**, not a storage vault. A vault is passive and gets abandoned; a readiness system has a job at a specific moment.

It lives in **two modes**:
- **Calm mode (before):** low-friction setup, family coordination, staying fresh. Fights *unpreparedness*.
- **Crisis mode (during):** dead-simple, instant, reachable-by-a-stranger. Fights *confusion*.

**One-line concept (pin this to the wall):**
> A readiness system that lets a family's coordinator prepare calmly once, keep it true over time, and lets whoever is present in a medical crisis act fast and correctly — without depending on the patient or the coordinator being able to help in that moment.

**North-star test for every future feature:** Does it either (a) lower the barrier to a family actually preparing, or (b) make the crisis moment work for someone who isn't the patient? If neither → it's scope creep.

## 3. Key design decisions (settled principles)
- **The coordinator is the user; design the output for the responder.** Never assume the patient is conscious or the coordinator is present.
- **Honesty over false freshness.** You can't guarantee data is current across a family. So don't pretend to — show each fact's age ("confirmed 8 months ago") so a reader knows how much to trust it. Stale data with false authority can be worse than no data.
- **Maintenance is "confirm or correct," not "keep perfect."** Confirmation is cheaper than entry. Hang updates off real-life events (a doctor visit, a policy renewal), not an arbitrary schedule.
- **Motivate with care and agency, never fear.** Fear fatigues or creates anxiety and gets avoided. "You've got this covered for the people you love" is sustainable for years.
- **Crisis mode is a script, not a data sheet.** A pro (paramedic) knows where to look; cede that lane. Your lane is the *frightened lay responder* who needs to be told what to do.
- **Data becomes words to say.** Store "allergic to penicillin"; render "Tell the doctor: she's allergic to penicillin." Zero interpretation for a panicking reader.
- **Steady, then instruct.** The first thing the crisis screen does is lower the reader's heart rate ("Take a breath. Do these in order."), then one step at a time.
- **Tiered access is also protection.** Open/scannable = help-only info that can only benefit the patient. Sensitive/exploitable info (full address, financials, ID) stays gated. A family in crisis is vulnerable to exploitation, so the script can include guard-rails ("your policy covers this as cashless — you should not be asked to pay upfront").
- **Reachability needs redundancy.** Lock-screen Medical ID, a QR on a card/fridge/car, a shareable link, a printed wallet card — each covers another's failure (dead battery, no phone, responder not present yet). The QR's specific job is the *"patient's phone is gone"* layer: a responder scans a physical object with their own phone and the crisis page opens. Its limits: it needs the responder's internet, it has to be found and clearly labelled ("MEDICAL EMERGENCY — SCAN ME"), and it should be per-person (on a wallet/phone), not on a shared surface. So it is one layer, not the whole answer.
- **The family alert is responder-triggered, not patient-triggered.** Since the patient may be unconscious, the crisis page carries a one-tap "Notify family" button. The stranger in the room presses it; the whole pre-configured contact circle is alerted with the patient's location (captured at the tap) and a secure link to details — never a raw dump of medical data into a message. (Later concerns: false-trigger/abuse friction, delivery acknowledgment, and escalation to the next contact.)

## 4. The system shape (design concept)
Everything collapses into **three surfaces joined by one core.**

**A. Coordinator surface (calm mode)** — authenticated, rich, patient. Build out family members, medical facts, contacts, insurance/logistics; do the periodic "confirm it's still right." Optimized for a motivated person with time.

**B. Crisis surface (crisis mode)** — no login, glanceable, reachable without your app installed (QR / link / lock screen). Renders the *script* plus only the open tier of data. Optimized for a frightened stranger with seconds.

**C. The core that joins them** — three intertwined problems and where the interesting engineering lives:
- **Calm-to-crisis transform:** store facts so they compose into spoken lines/actions.
- **Tiered no-auth-but-private access:** public read of the safe subset, gate on the rest, revocable tokens, logged scans.
- **Confidence as first-class metadata:** every fact carries "last confirmed" and surfaces its own staleness, end to end.

## 5. How to actually build this (the process)
You asked whether to fully design + architect everything before building. Short answer: **no — that's waterfall, and it kills beginner projects.** You can't correctly design what you haven't built; many decisions only become real in code. Instead:

1. Concept clear ✅ (sections 1–4).
2. Pick the **smallest meaningful slice** that works end-to-end.
3. Design *only that slice*.
4. Build it. Get it running.
5. Learn from what broke. Expand by one slice.
6. Repeat. The architecture grows with the code.

A useful term: a **walking skeleton** — the thinnest possible version that connects every layer end to end (data → logic → output), even if each layer is trivial. You build the skeleton first, then add muscle.

> Safety note while learning: use **fake data**, not your real family's medical records, until you've actually built the access controls. A learning prototype is not a safe place for real medical/insurance info.

## 6. Proposed first slice (the walking skeleton)
The smallest thing that proves the soul of the concept — the calm→crisis pipe:

- Store **one person's** critical facts: name, one emergency contact + phone, allergies, current meds, one major condition.
- A simple coordinator way to enter/edit those facts. (Skip login for slice 1 — single user, local. Auth is a later slice.)
- A **public crisis page** at a unique URL that renders those facts as a basic script:
  > "Take a breath. Call **[contact]** at **[phone]**. Tell the doctor: allergic to **[X]**, takes **[Y]**, has **[Z]**."

That's it. **No** QR yet (a QR is just an encoding of that URL — add it later). **No** tiers, documents, insurance, or freshness yet. This one slice already demonstrates: two surfaces (edit vs. crisis view) + the calm-to-crisis transform.

> The walking skeleton is the *first build step*, not the whole prototype. The full prototype — the version that conveys the entire concept in a 60-second demo — grows from this skeleton by adding a few concept-conveyors (a second family member, a logistics guard-rail line, a QR, the responder-triggered "Notify family" button, a "last confirmed" date, a tiering hint). That fuller scope and its build order live in **`prototype-spec.md`**.

## 7. Light architecture — for the first slice only
*(Later slices get their own design when you reach them.)*

- A small web service. (You're comfortable with Python/Node → FastAPI or Express is fine.)
- A data store. **Start simple** — even SQLite or a single JSON file is okay for slice 1. Swap to Postgres in a later slice when you actually need it.
- One data model: `Person` with the fields above.
- Two routes:
  - coordinator edit (a form or simple API),
  - public crisis view (renders the script from the data).
- The **transform** is just a function/template in the crisis view that turns `Person` fields into script sentences. This is the conceptual heart — keep it isolated so it's easy to grow.

## 8. What comes after (a roadmap of *slices*, not a feature dump)
Each slice teaches one concept. Design each only when you reach it:
1. Walking skeleton (above).
2. Add real persistence (move to Postgres) + basic auth for the coordinator.
3. Support multiple family members.
4. Add the **tiered access model**: unique tokens, public-safe view vs. gated view, revoke + log scans. (Then a QR is trivial.)
5. Add **confidence timestamps** ("last confirmed") on every fact, surfaced everywhere.
6. Add **freshness nudges** (care-and-agency framed "confirm or correct").
7. Add documents + insurance/logistics tier + the protective guard-rails.
8. Add offline/degradation on the crisis surface (works on flaky networks / as a PWA).

## 9. Open questions & known risks (carry these forward)
- **Guard-rail vs. liability line:** the script protecting a vulnerable family is powerful, but if it's ever wrong (stale insurance, dropped empanelment) you've misled someone at the worst moment. Mitigation in spirit: confidence timestamps + "verify at the desk" framing keeps you on the *guide* side.
- **Staleness** is the central ongoing risk — honesty (timestamps) is the defense, not a promise of freshness.
- **The behavioral wall:** even a perfect tool fails if families won't do the calm-mode setup. (Not your problem for a learning build, but real if it ever becomes a product.)
- **Language:** entered in one language, read by a responder in another. Worth a thought eventually.
- **QR depends on the responder's internet and on being found/placed.** It fails on weak signal or if the coordinator never printed/placed it. Mitigate with a tiny, fast crisis page; true offline would mean baking bare basics into the code itself, trading away richness and freshness.
- **The alert can misfire or be abused.** A public "Notify family" trigger can be tapped by accident or spammed (and real SMS costs money). Eventually needs light friction, rate-limiting, acknowledgment, and escalation — out of scope for the prototype.
