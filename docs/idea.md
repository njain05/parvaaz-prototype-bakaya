# Idea: Bakaya, an AI credit tracker for machinery makers

## The problem

We interviewed the owner of a textile-machinery manufacturer with about 15–20 workers. They build large,
made-to-order machines worth ₹5–25 lakh each.

Asked what the biggest problem is for them as the owner, they said **credit**: collecting money that customers owe.

- Machines are sold on **instalments**, typically an advance, a payment before dispatch, and a final payment after installation.
- Customers often **pay late**, and keeping track of who owes what across many orders is hard.
- Following up has to stay **polite**, because these are long-term customer relationships built on trust and word of mouth.

## The solution

**Bakaya** (बकाया, meaning "dues outstanding") is a simple web app where the owner can:

- See at a glance **how much money is outstanding**, how much is **overdue**, and what's **due this week**
- See **who owes what** and for how long, with each customer labelled *Pays on time*, *Sometimes late* or *Often late*
- Record each machine order with its **payment plan**, and record payments as they come in

## Where AI helps

| Feature | How it helps the owner |
| --- | --- |
| **Payment reminders** | AI writes a polite WhatsApp reminder in **Hinglish, Hindi, Punjabi or English**. The tone gets firmer the later the payment is. The owner reviews it, then sends it with one tap. |
| **Ask in plain language** | Ask questions like *"Sabse zyada paisa kiska baaki hai?"* and get an answer from their own data. |
| **Scan a bill** | Take a photo of an invoice and the AI fills in the new order. No typing needed. |

## Why this idea

- It's the problem the owner said is **biggest** for them.
- It can be solved with **software alone**, with no hardware or factory changes.
- The **owner stays in control**: the owner was skeptical of bots messaging customers automatically, so every reminder is reviewed by them before it goes out.
- It works in the **languages they actually use**.

## Who it's for

Owners of small and medium manufacturing businesses that sell expensive goods on credit or instalments.
The first target is machinery makers in Punjab's textile and industrial clusters.

## Next steps

1. Factory visit: find out how they track credit today (Tally, Excel, a notebook?) and how much money is stuck.
2. Show them the prototype and record their feedback in the [feedback log](feedback-log.md).
3. Improve the prototype based on that feedback.

The working prototype is in this repository. See the [main README](../README.md) to run it.
