# Idea: Bakaya, a follow-up assistant for machinery makers

## The problem

We interviewed the owner of a textile-machinery manufacturer with about 15–20 workers. They build large,
made-to-order machines worth ₹5–25 lakh each.

Asked what the biggest problem is for them as the owner, they said **credit**: collecting money that customers owe.

- Machines are sold on **instalments**, typically an advance, a payment before dispatch, and a final payment after installation.
- Customers often **pay late**, and keeping track of who owes what across many sales is hard.
- Following up has to stay **polite**, because these are long-term customer relationships built on trust and word of mouth.
- Automated daily messages to customers get ignored or arrive at bad times, so the owner wants to stay in control
  of what is sent.

## The solution

**Bakaya** (बकाया, meaning "dues outstanding") is a **follow-up assistant**. The owner opens it on their phone,
sees **who to contact today and why**, and sends the message in one tap.

- **Today:** one line of totals (*₹55.7 lakh owed to you · ₹24.2 lakh late*), then the customers to contact, each
  with a reason: *"Promised ₹5 lakh by 19 Nov. Not received."* or *"60 days late. Reminded 9 days ago, no payment yet."*
- **The app remembers every follow-up.** A customer who was just reminded, or who promised to pay by a date that
  hasn't come yet, leaves Today until it's time to follow up again. A broken promise brings them back to the top.
- **Customer page:** what they owe, their payment habit (*Usually pays about 31 days late*), each machine with its
  instalments, and one history of payments, reminders and promises.
- **Recording is quick:** a payment received, a promise to pay, or a new sale with the usual 30/60/10 plan
  filled in.

## Where AI helps

| Feature | How it helps the owner |
| --- | --- |
| **Payment reminders** | AI writes a polite WhatsApp reminder in **Hinglish, Hindi, Punjabi or English**. The tone gets firmer the later the payment is, and firmer again if earlier reminders went unanswered. The owner checks it, then sends it on WhatsApp. |
| **Ask in plain language** | Ask questions like *"Who promised to pay?"* or *"Sabse zyada paisa kiska baaki hai?"* and get an answer from their own data. |
| **Scan a bill** | Take a photo of an invoice and the AI fills in the new sale. No typing needed. |

The reasons on Today come from fixed rules, not from the AI, so the amounts and dates are always right. Without an
API key the app still works: reminders come from templates and Ask answers simple questions.

## Built in stages

The same Today list grows with each stage, so the owner keeps one place to look.

1. **Credit (now):** who to remind about late payments, and why. This is the owner's biggest problem.
2. **Service (next):** *"Kaur Hosiery's tumble dryer is due for servicing"*. Needs an installation date per sale
   and a service interval per machine type.
3. **Upsell and enquiries (later):** suggest a newer machine to past buyers, and follow up on enquiries from new
   customers.

## Why this idea

- It's the problem the owner said is **biggest** for them.
- It can be solved with **software alone**, with no hardware or factory changes.
- The **owner stays in control**: they were skeptical of bots messaging customers automatically, so every reminder
  is checked by them before it goes out.
- It works in the **languages they actually use**, on the **phone they already use** for WhatsApp.

## Who it's for

Owners of small and medium manufacturing businesses that sell expensive goods on credit or instalments.
The first target is machinery makers in Punjab's textile and industrial clusters.

## Next steps

1. Factory visit: show the owner the prototype, find out how they track credit today (Tally, Excel, a notebook?)
   and how much money is stuck.
2. Record their feedback in the [feedback log](feedback-log.md).
3. Improve the prototype based on that feedback, then start stage 2 (service reminders).

The working prototype is in this repository. See the [main README](../README.md) to run it.
