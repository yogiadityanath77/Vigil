---
description: Read-only review of the current slice against the project docs and decisions
argument-hint: [optional base ref, e.g. slice2 or HEAD~3]
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(git status:*)
---

You are REVIEWING code, not writing it. Do NOT edit, create, or fix any files —
only report findings. Be direct; if something is wrong, say so plainly. Don't be agreeable.

Recent history:
!`git log --oneline -20`

Working tree status:
!`git status --short`

## Task
1. Identify the commits in the CURRENT slice. If I passed a base ref ("$ARGUMENTS"),
   diff from there; otherwise infer the slice boundary from the log above and the Status
   section of CLAUDE.md, then run `git diff <base>..HEAD`.
2. Audit ONLY that diff against docs/prototype-spec.md (scope + order) and docs/DECISIONS.md.

## Checks — report each as PASS or PROBLEM
- D5: are medical_facts and emergency_contacts edited via granular, identity-preserving
  endpoints (per-item POST/PATCH/DELETE), NOT full-replace?
- Is all input validated via Pydantic, and are all queries parameterized (ORM / bound params)?
- Are secrets read only from env — no literals, nothing committed?
- Is crisis_slug generation in ONE place, not duplicated between seed.py and the create path?
- Is the "no auth yet — local only" boundary explicit in code/comments on the write endpoints?
- Did anything from a LATER slice leak in (multi-person list, frontend, QR, notify, timestamps)?
- Is the fact→sentence transform still pure and isolated (no DB / HTTP / side effects)?
- Do tests cover the new write paths and assert the right behavior?

## Output
Group findings by severity: BLOCKER / SHOULD-FIX / NITPICK. For each, name the file and line,
what's wrong, and why it matters downstream. End with a one-line verdict: ready for the next
slice, or not yet. Change nothing.