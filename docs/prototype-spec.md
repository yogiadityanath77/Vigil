# Prototype Spec — Family Medical Readiness System
*(companion to `medical-readiness-design.md` — read that first for the concept)*

## Purpose of this prototype
This is **not** production and **not** the final product. Its only job is to **convey the whole concept** convincingly and to be something you learn from while building. So the test for putting anything in is not "is it useful?" — it's **"does it make one of our core concepts visible?"** Cheap things that sell a concept (a line of copy, one date field, a QR) earn their place; expensive production plumbing waits.

> While building, use **fake data** — never your real family's medical or insurance details — because the prototype has no real security yet.

## The success test (the moment to aim for)
If you hand someone a QR, let them scan it as if they were a panicking stranger, and they:
1. read a **calm script** that tells them exactly what to do and say,
2. see an **insurance guard-rail** ("covered as cashless — don't pay upfront"),
3. tap **one button to alert the family** with the patient's location,
4. notice the info **knows its own age** ("confirmed 3 weeks ago"),

…then they understand the entire concept in under a minute. **That "oh, I get it" moment is the prototype's deliverable.** Anything that doesn't contribute to it is a candidate to cut.

## What's IN — and the concept each thing conveys

### Real (but minimal) features
- **Two surfaces** — a calm setup screen *and* a separate public crisis screen. → *Conveys the two-mode concept; without both you've shown nothing.*
- **At least two family members** — not one. → *Conveys the family-coordination angle that separates this from phone Medical ID.*
- **The crisis script** — opens with a steadying line, then renders the person's facts as pre-composed sentences to say and do. → *Conveys "crisis = script not data sheet," "data becomes words," and "steady then instruct" all at once. This is the signature screen.*
- **One logistics element** — insurance/policy + hospital, surfaced as a guard-rail line in the script. → *Conveys the logistics-awareness that is the actual gap.*
- **The "Notify family" button** — responder-triggered, simulated send, location captured at the tap. → *Conveys "reaches whoever's in the room and mobilizes the circle."*

### Cheap concept-conveyors (don't skip — they cost almost nothing)
- **A QR code** encoding the crisis URL. → *Sells the reachability idea in two seconds at demo time.*
- **A "last confirmed [date]"** on the facts. → *One field that conveys the entire honesty/confidence principle.*
- **A two-level hint** — the open help-only script vs. a "details for family" view with more. (Shown, not really secured yet.) → *Conveys the tiering/protection concept.*
- **Care-and-agency tone** in all copy. → *A core principle, and it's free.*

## What's OUT — and why leaving it out doesn't weaken the idea
- **Real auth + true token security/gating** — the prototype *demonstrates* tiering and reachability; production security is a later craft.
- **Real SMS/WhatsApp + escalation/acknowledgment** — a *simulated* send conveys the full idea; the plumbing is a later slice. (In India, WhatsApp is the eventual right channel but its API is harder; SMS is the reliable workhorse.)
- **The freshness *nudge loop*** — the timestamp display already conveys the honesty principle; the reminder engine is a behavior you build later.
- **Document uploads** — that's storage, and we're explicitly *not* a vault; structured facts + the script carry the idea.
- **Offline/PWA, multiple accounts/families** — reliability and scale concerns, not concept-conveyors.

## How the QR works (in the prototype, and its real-world role)
Mechanically, a QR is just an **encoded URL**. Any modern phone camera scans it and opens that link — no app needed on the scanner's side. So each person's QR encodes *their* crisis-page URL (use an unguessable slug like `/c/8f3k9d2`).

To build/test it in the prototype: generate the QR from the URL (a `qrcode` library in Python or Node), display it on screen, and scan it with a phone — it opens the crisis page. That's a complete, demoable QR flow.

Its real-world role (carry forward, don't build the hard parts yet): the QR is the **"patient's phone is gone"** layer — a responder scans a physical card/sticker with *their own* phone. Its limits, which is why it's only one layer of several: it needs the responder's internet, it must be found and clearly labelled ("MEDICAL EMERGENCY — SCAN ME"), and it belongs on a personal item, not a shared fridge.

## The "Notify family" flow (responder-triggered)
1. Responder taps **"Notify family"** on the crisis page.
2. The page asks the browser for its **current location** (permission prompt) and attaches it.
3. The system "sends" to each pre-configured contact — **for the prototype, simulate this**: log the message and show a "Sent ✓" confirmation. The message is light: *"Emergency involving [name]. Location: [map link]. Details: [secure link]."*
4. The **secure link**, not a raw data dump, is what carries the richer details — keeps sensitive info out of the message itself.

(Real SMS/WhatsApp, plus false-trigger friction, delivery acknowledgment, and escalation to the next contact, are all later.)

## Suggested build order (each step runs end-to-end)
Build in this order so something works early and every step adds exactly one concept:
1. **Walking skeleton** — one `Person` (simple store), a public crisis page that renders their facts as a basic script. Get it running.
2. Make the crisis page proper — steadying opener + ordered, pre-composed sentences.
3. Add a simple coordinator edit screen/API to change the facts.
4. Add a **second family member** (a list + a per-person crisis URL).
5. Add the **logistics field** + the guard-rail line in the script.
6. Generate a **QR** per person from the crisis URL; test by scanning with a phone.
7. Add the **"Notify family"** button → simulated send + browser location + the secure-link idea.
8. Add **"last confirmed [date]"** display on the facts.
9. Add the **two-level hint** (open script vs. "for family" richer view).
10. Pass over all copy for **care-and-agency tone**.

## What you'll need (light tech — you choose, Python/Node both fine)
- A small web service (FastAPI or Express).
- A simple data store to start — SQLite or even a JSON file is fine; swap to Postgres later when you actually need it.
- A QR library (`qrcode` in Python, `qrcode` in npm).
- The browser **Geolocation API** for the notify location.
- Simple templating for the crisis page.
- Keep the **fact → sentence transform** isolated in its own function/template — it's the conceptual heart and you'll grow it.

## How to demo it
Open the coordinator screen, fill in two family members (fake data). Print or display one person's QR. Hand your phone to a friend and say "you just walked in on an emergency — scan this." Let them experience the calm script, the guard-rail, and the one-tap family alert. If they "get it" without you explaining — the prototype succeeded.
