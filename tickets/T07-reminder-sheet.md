# T07 — Reminder sheet: draft, edit, send on WhatsApp, log, undo
**Status:** DONE
**Prereqs:** T04, T06 · **Branch:** t07-reminder-sheet

## Goal

From anywhere in the app, the owner can open a reminder for a customer, pick the language, edit the draft, and
send it on WhatsApp in one tap. Sending records the reminder in the contact log, with an Undo in case they didn't
actually send it.

Interface track: T06 → T07 → T08 (Today) and T09 (customer page). PLAN.md §Send reminder, §Assumed 2.

## Scope / files

- `static/js/reminder.js`: replace the stub with `openReminder(customerId, orderId, {onSent} = {})`.
- `static/style.css`: only the `/* ===== screen: reminder ===== */` section.

## Details

- Opens with `openSheet`. Header: customer name, and the machine and amount the reminder is about.
- Language switch as four buttons in a row: Hinglish · हिंदी · ਪੰਜਾਬੀ · English. Remember the choice with
  `store("lang")`, default Hinglish.
- Draft: `POST /api/ai/reminder {order_id, language}` (shape unchanged). While waiting: "Writing…". Under the text
  a small line: "Written by AI. Check it before sending." or "Written from a template." plus any `note`.
  A **Rewrite** text button asks again.
- **Send on WhatsApp**: `window.open(whatsappUrl(phone, text), "_blank")`, then
  `POST /api/customers/<customerId>/contacts {kind: "reminder", order_id, language}`, close the sheet, call
  `onSent()`, and `toast("Reminder sent to {name}", {action: {label: "Undo", onClick}})`. Undo calls
  `DELETE /api/contacts/<id>`, then `onSent()` again so the screen refreshes, and toasts "Reminder removed".
- If logging fails, the message has still gone to WhatsApp: toast "Sent, but couldn't save it in the history:
  {error}".
- Errors from the draft request show in the sheet, with Rewrite still available.

- Done as built: the sheet title is "Reminder to {name}" (as in the mockup), with the late or due amount and the
  machine underneath, and the message label names the contact person. If the sale isn't the customer's, or the
  customer can't be loaded, the sheet shows that in the header and Send stays disabled. Send is also disabled
  while a draft is being written or the message is empty. Switching language or tapping Rewrite while a draft is
  still loading ignores the older reply.

## Tests

manual: see Check

## Check

The Today and customer screens are still stubs, so open it from the browser console on http://localhost:5055:

```js
const m = await import("/static/js/reminder.js"); m.openReminder(1, 1, {onSent: () => console.log("sent")})
```

Switch to ਪੰਜਾਬੀ (the draft changes), edit the text, Send on WhatsApp: a WhatsApp tab opens with the text, the toast
shows with Undo, and `curl localhost:5055/api/customers/1` has the reminder in `history`. Undo: it's gone.

## Done when

- [x] `openReminder` drafts, switches language, rewrites, and sends to WhatsApp
- [x] Sending logs a reminder contact; Undo deletes it
- [x] Works at 390px and on desktop, light and dark
- [x] Committed: `T07: reminder sheet with WhatsApp send, log and undo`
