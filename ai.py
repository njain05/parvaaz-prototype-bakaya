"""Claude-powered features: payment reminders, questions about the credit book, and reading bills.

Every function raises AIError on failure so the server can fall back to offline mode.
"""
import base64
import json
import os

import anthropic

MODEL = "claude-opus-5-5"
# If the model declines a request, the API retries it on a fallback model inside the same call.
BETAS = ["server-side-fallback-2026-07-01"]

_client = None


class AIError(Exception):
    pass


def enabled():
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _call(system, content, effort="low", schema=None):
    output_config = {"effort": effort}
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    try:
        resp = _get_client().beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=BETAS,
            fallbacks="default",
            system=system,
            messages=[{"role": "user", "content": content}],
            output_config=output_config,
        )
    except anthropic.AuthenticationError:
        raise AIError("The API key in .env was rejected.")
    except anthropic.RateLimitError:
        raise AIError("Too many requests right now. Try again in a minute.")
    except anthropic.APIConnectionError:
        raise AIError("Couldn't reach the Claude API. Check the internet connection.")
    except anthropic.APIStatusError as e:
        raise AIError(f"Claude API error ({e.status_code}).")

    if resp.stop_reason == "refusal":
        raise AIError("The AI declined this request.")
    if resp.stop_reason == "max_tokens":
        raise AIError("The AI's answer was cut off.")
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not schema:
        return text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise AIError("The AI returned an unreadable answer.")


LANGUAGES = {
    "english": "English",
    "hinglish": "Hinglish (Hindi written in Roman letters, mixed with common English words, as people write on WhatsApp)",
    "hindi": "Hindi in Devanagari script",
    "punjabi": "Punjabi in Gurmukhi script",
}

REMINDER_SYSTEM = """You write WhatsApp payment reminders for an Indian textile-machinery manufacturer. \
The readers are business owners who bought expensive machines on instalments, and the relationship matters.

Rules:
- Respectful and warm: address the person with "ji". Never threatening, never mention legal action.
- Match the tone to how late the payment is: under 15 days is a gentle nudge, 15 to 45 days is firm, \
over 45 days is serious and asks them to call today to confirm a payment date. \
A payment that is not yet due gets a friendly heads-up.
- Mention the machine, the order number, the exact amount and the due date given in the facts. Invent nothing.
- Ask them to pay or to share an expected payment date.
- At most 70 words. Sign off with the business name.
- Output only the message text, nothing else."""


def draft_reminder(facts, language):
    lang = LANGUAGES.get(language, LANGUAGES["english"])
    content = f"Write the reminder in {lang}.\n\nFacts:\n{json.dumps(facts, ensure_ascii=False, indent=2)}"
    return _call(REMINDER_SYSTEM, content, effort="low")


ASK_SYSTEM = """You help the owner of a textile-machinery company understand their credit book: \
which customers owe money, what is overdue and what is due soon.

Rules:
- Answer only from the data provided. If the data doesn't answer the question, say so.
- Write money in rupees with Indian grouping (₹12,34,567) and say lakh where it helps (₹12.3 lakh).
- Be short: a sentence or two, or a short bullet list when listing customers.
- Reply in the language and script of the question (English, Hindi, Hinglish or Punjabi)."""


def answer_question(question, snapshot):
    content = (
        f"Credit book data (today is {snapshot['today']}):\n"
        f"{json.dumps(snapshot, ensure_ascii=False)}\n\nOwner's question: {question}"
    )
    return _call(ASK_SYSTEM, content, effort="medium")


BILL_SCHEMA = {
    "type": "object",
    "properties": {
        "is_bill": {"type": "boolean"},
        "customer_name": {"type": "string"},
        "contact_person": {"type": "string"},
        "phone": {"type": "string"},
        "city": {"type": "string"},
        "invoice_number": {"type": "string"},
        "invoice_date": {"type": "string"},
        "item": {"type": "string"},
        "total_amount": {"type": "number"},
        "amount_paid": {"type": "number"},
    },
    "required": ["is_bill", "customer_name", "contact_person", "phone", "city",
                 "invoice_number", "invoice_date", "item", "total_amount", "amount_paid"],
    "additionalProperties": False,
}

BILL_SYSTEM = """You read photos of bills, invoices and quotations from an Indian machinery manufacturer \
and extract the details needed to record a sale.

- customer_name is the BUYER (billed to / consignee), not the company that issued the bill.
- item is the main machine or goods sold, in a few words.
- total_amount is the grand total in rupees, including GST. amount_paid is any advance or amount \
shown as received, else 0.
- invoice_date as YYYY-MM-DD.
- Use an empty string or 0 for anything not on the bill. Do not guess.
- If the image is not a bill or invoice, set is_bill to false."""


def read_bill(image_bytes, media_type):
    data = base64.standard_b64encode(image_bytes).decode("utf-8")
    content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
        {"type": "text", "text": "Extract the sale details from this bill."},
    ]
    return _call(BILL_SYSTEM, content, effort="medium", schema=BILL_SCHEMA)
