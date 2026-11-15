# T05 — Reminders and Ask use the contact log
**Status:** TODO
**Prereqs:** T02 · **Branch:** t05-ai-uses-contacts

## Goal

A second reminder to the same customer is one step firmer than the first, both from the AI and from the offline
templates. Ask AI can answer questions about reminders and promises ("Who promised to pay?", "Sharma ko kab
remind kiya tha?").

Data track: T02 → T05 → T12. PLAN.md §Today rules 7, §Assumed 4.

## Scope / files

- `app.py`: edit only `reminder_facts` and `ai_snapshot` (T03 and T04 add routes elsewhere in the file).
  - `reminder_facts` adds `"reminder_count": contact_log.reminder_count(data, customer_id)`.
  - `ai_snapshot` adds per customer: `reminders_since_last_payment`, `last_reminder_date`, and `promise`
    (`promise_status`, or null).
- `offline.py`: `tone_for(days_overdue, reminder_count=0)`; `template_reminder` passes `facts["reminder_count"]`.
  `answer()` handles promise questions.
- `ai.py`: `REMINDER_SYSTEM` explains `reminder_count`; `ASK_SYSTEM` mentions reminders and promises in the data.
- New `tests/test_reminders.py`.

## Details

- Tone steps: `upcoming` < `gentle` < `firm` < `serious`. Start from days late as now, then go up one step per
  earlier reminder, capped at `serious`. A not-yet-due payment stays `upcoming` whatever the count.
- AI prompt addition: "`reminder_count` is how many reminders were already sent since the customer's last payment.
  For each one, be one step firmer than the days late alone suggest, never beyond 'serious'. Still never threaten."
- Offline `answer()`: keywords `promise`, `promised`, `wada`, `vaada`, `vada` → list customers with an open or
  broken promise: `"{name}: {inr(amount)} by {date} (broken)"` / `(open)`. None → `"No one has an open promise
  to pay."` Put this check before the existing keyword checks (after the customer-name check).
- The `/api/ai/reminder` request and response shapes do not change (T07 builds against them).

## Tests

`tests/test_reminders.py` (offline; conftest removes the API key):

- `tone_for(10, 0) == "gentle"`, `tone_for(10, 1) == "firm"`, `tone_for(10, 5) == "serious"`,
  `tone_for(0, 3) == "upcoming"`
- `POST /api/ai/reminder` for Sharma's order uses one step firmer than the same request with Sharma's reminder
  deleted (compare against the template text for each tone)
- `offline.answer("who promised to pay?", …)` names Shree Ganesh (broken) and Arora (open)

## Check

```bash
.venv/bin/python -m pytest -q tests/test_reminders.py
curl -s -X POST localhost:5055/api/ai/ask -H 'Content-Type: application/json' -d '{"question":"Who promised to pay?"}'
```

## Done when

- [ ] Reminder tone rises with `reminder_count` in templates and in the AI prompt
- [ ] Ask (offline and AI) can answer promise questions
- [ ] `tests/test_reminders.py` passes, and so does the whole suite
- [ ] Committed: `T05: reminders and Ask use the contact log`
