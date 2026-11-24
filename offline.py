"""Offline fallbacks so the demo still works without an API key or internet:
template reminders in four languages and keyword-based answers to common questions."""
from ledger import inr, nice_date

TEMPLATES = {
    "english": {
        "upcoming": "Namaste {person} ji, a friendly reminder from {biz}: {amt} for the {machine} (order #{id}) is due on {due}. Thank you for your continued support!",
        "gentle": "Namaste {person} ji, a gentle reminder from {biz}. {amt} for the {machine} (order #{id}) was due on {due}. Kindly arrange the payment at your convenience, or let us know the expected date. Thank you!",
        "firm": "Namaste {person} ji, {amt} for the {machine} (order #{id}) has been pending since {due} ({days} days). Please arrange the payment this week, or share a confirmed date. Regards, {biz}",
        "serious": "Namaste {person} ji, {amt} for the {machine} (order #{id}) is now overdue by {days} days (due {due}). We request you to clear it at the earliest, as it is affecting our production schedule. Please call us today to confirm the payment date. Regards, {biz}",
    },
    "hinglish": {
        "upcoming": "Namaste {person} ji, {biz} ki taraf se reminder: {machine} (order #{id}) ka {amt} payment {due} ko due hai. Aapke saath ke liye dhanyavaad!",
        "gentle": "Namaste {person} ji, {biz} ki taraf se ek chhota sa reminder. {machine} (order #{id}) ka {amt} payment {due} ko due tha. Jab convenient ho payment kar dijiye, ya expected date bata dijiye. Dhanyavaad!",
        "firm": "Namaste {person} ji, {machine} (order #{id}) ka {amt} payment {due} se pending hai ({days} din). Kripya is hafte payment arrange kar dijiye, ya confirm date bata dijiye. – {biz}",
        "serious": "Namaste {person} ji, {machine} (order #{id}) ka {amt} payment {days} din se overdue hai (due date {due}). Kripya jaldi se jaldi clear kar dijiye, isse humara production schedule affect ho raha hai. Aaj call karke payment date confirm kar dijiye. – {biz}",
    },
    "hindi": {
        "upcoming": "नमस्ते {person} जी, {biz} की ओर से याद दिला रहे हैं: {machine} (ऑर्डर #{id}) का {amt} का भुगतान {due} को देय है। आपके सहयोग के लिए धन्यवाद!",
        "gentle": "नमस्ते {person} जी, {biz} की ओर से एक छोटा सा रिमाइंडर। {machine} (ऑर्डर #{id}) का {amt} का भुगतान {due} को देय था। सुविधा अनुसार भुगतान कर दीजिए, या संभावित तारीख बता दीजिए। धन्यवाद!",
        "firm": "नमस्ते {person} जी, {machine} (ऑर्डर #{id}) का {amt} का भुगतान {due} से बकाया है ({days} दिन)। कृपया इस सप्ताह भुगतान की व्यवस्था करें, या पक्की तारीख बता दें। – {biz}",
        "serious": "नमस्ते {person} जी, {machine} (ऑर्डर #{id}) का {amt} का भुगतान {days} दिनों से बकाया है (देय तिथि {due})। कृपया जल्द से जल्द भुगतान करें, इससे हमारा उत्पादन कार्यक्रम प्रभावित हो रहा है। आज ही कॉल करके भुगतान की तारीख पक्की करें। – {biz}",
    },
    "punjabi": {
        "upcoming": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ {person} ਜੀ, {biz} ਵੱਲੋਂ ਯਾਦ ਕਰਵਾ ਰਹੇ ਹਾਂ: {machine} (ਆਰਡਰ #{id}) ਦਾ {amt} ਦਾ ਭੁਗਤਾਨ {due} ਨੂੰ ਹੋਣਾ ਹੈ। ਤੁਹਾਡੇ ਸਹਿਯੋਗ ਲਈ ਧੰਨਵਾਦ!",
        "gentle": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ {person} ਜੀ, {biz} ਵੱਲੋਂ ਇੱਕ ਛੋਟੀ ਜਿਹੀ ਯਾਦ-ਦਹਾਨੀ। {machine} (ਆਰਡਰ #{id}) ਦਾ {amt} ਦਾ ਭੁਗਤਾਨ {due} ਤੱਕ ਹੋਣਾ ਸੀ। ਕਿਰਪਾ ਕਰਕੇ ਸਹੂਲਤ ਅਨੁਸਾਰ ਭੁਗਤਾਨ ਕਰ ਦਿਓ, ਜਾਂ ਸੰਭਾਵਿਤ ਤਾਰੀਖ ਦੱਸ ਦਿਓ। ਧੰਨਵਾਦ!",
        "firm": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ {person} ਜੀ, {machine} (ਆਰਡਰ #{id}) ਦਾ {amt} ਦਾ ਭੁਗਤਾਨ {due} ਤੋਂ ਬਕਾਇਆ ਹੈ ({days} ਦਿਨ)। ਕਿਰਪਾ ਕਰਕੇ ਇਸ ਹਫ਼ਤੇ ਭੁਗਤਾਨ ਕਰ ਦਿਓ, ਜਾਂ ਪੱਕੀ ਤਾਰੀਖ ਦੱਸ ਦਿਓ। – {biz}",
        "serious": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ {person} ਜੀ, {machine} (ਆਰਡਰ #{id}) ਦਾ {amt} ਦਾ ਭੁਗਤਾਨ {days} ਦਿਨਾਂ ਤੋਂ ਬਕਾਇਆ ਹੈ (ਤਾਰੀਖ {due})। ਕਿਰਪਾ ਕਰਕੇ ਜਲਦੀ ਤੋਂ ਜਲਦੀ ਭੁਗਤਾਨ ਕਰੋ, ਇਸ ਨਾਲ ਸਾਡਾ ਉਤਪਾਦਨ ਪ੍ਰਭਾਵਿਤ ਹੋ ਰਿਹਾ ਹੈ। ਅੱਜ ਹੀ ਫ਼ੋਨ ਕਰਕੇ ਭੁਗਤਾਨ ਦੀ ਤਾਰੀਖ ਪੱਕੀ ਕਰੋ। – {biz}",
    },
}


TONES = ["upcoming", "gentle", "firm", "serious"]


def tone_for(days_overdue, reminder_count=0):
    """The reminder tone: from days late, then one step firmer per earlier reminder, never past 'serious'.
    A payment that is not yet due stays 'upcoming' however often it was mentioned."""
    if days_overdue <= 0:
        return "upcoming"
    if days_overdue < 15:
        step = 1
    elif days_overdue <= 45:
        step = 2
    else:
        step = 3
    return TONES[min(step + reminder_count, len(TONES) - 1)]


def greeting_name(contact_person, fallback):
    """'Rajesh Sharma' -> 'Rajesh' (as in 'Rajesh ji'); keeps names like 'S. Kumar' whole."""
    parts = (contact_person or "").split()
    if not parts:
        return fallback
    return parts[0] if len(parts[0].rstrip(".")) > 1 else contact_person


def template_reminder(facts, language):
    t = TEMPLATES.get(language, TEMPLATES["english"])[tone_for(facts["days_overdue"], facts.get("reminder_count", 0))]
    return t.format(
        person=greeting_name(facts["contact_person"], facts["customer"]),
        biz=facts["business_name"],
        amt=facts["amount_due"],
        machine=facts["machine"],
        id=facts["order_id"],
        due=facts["due_date"],
        days=facts["days_overdue"],
    )


def _bullets(lines):
    return "\n".join(f"• {line}" for line in lines)


PROMISE_WORDS = ("promise", "promised", "wada", "vaada", "vada")


def promise_answer(people):
    """People with an open or broken promise to pay, one line each. `people` are ai_snapshot() customers."""
    rows = [
        f"{p['name']}: {inr(p['promise']['amount'])} by {nice_date(p['promise']['promised_date'])} "
        f"({p['promise']['state']})"
        for p in people
        if p.get("promise") and p["promise"]["state"] in ("open", "broken")
    ]
    if not rows:
        return "No one has an open promise to pay."
    return "Promises to pay:\n" + _bullets(rows)


def answer(question, book, people=()):
    """A keyword answer. `people` are the ai_snapshot() customers, which carry the contact log facts."""
    q = question.lower()
    customers = book["customers"]
    t = book["totals"]

    for c in customers:
        first = c["name"].split()[0].lower()
        if len(first) > 2 and first in q:
            if c["outstanding"] <= 0.5:
                return f"{c['name']} has no pending payments."
            line = f"{c['name']} owes {inr(c['outstanding'])} in total."
            if c["overdue"] > 0.5:
                line += f" {inr(c['overdue'])} of that is late (the oldest by {c['days_overdue']} days)."
            return line

    def has(*words):
        return any(w in q for w in words)

    if has(*PROMISE_WORDS):
        return promise_answer(people)

    if has("week", "hafte", "hafta", "upcoming", "aane", "soon", "next"):
        rows = []
        for o in book["orders"]:
            for m in o["milestones"]:
                if m["status"] == "upcoming" and m["due_date"] <= book["week_end"]:
                    rows.append(f"{o['customer_name']}: {inr(m['unpaid'])} ({m['label'].lower()}, due {nice_date(m['due_date'])})")
        if not rows:
            return "No payments are due in the next 7 days."
        return f"Due in the next 7 days ({inr(t['due_this_week'])}):\n" + _bullets(rows)

    if has("most", "sabse", "zyada", "jyada", "biggest", "top", "highest", "maximum"):
        top = sorted(customers, key=lambda c: -c["outstanding"])[:3]
        return "Customers who owe the most:\n" + _bullets(
            f"{c['name']}: {inr(c['outstanding'])}" + (f" ({inr(c['overdue'])} late)" if c["overdue"] > 0.5 else "") for c in top if c["outstanding"] > 0.5
        )

    if has("overdue", "late", "pending", "baaki", "baki", "bakaya", "due"):
        late = [c for c in customers if c["overdue"] > 0.5]
        if not late:
            return "Nothing is late right now."
        who = "1 customer is" if len(late) == 1 else f"{len(late)} customers are"
        return f"{who} late, {inr(t['overdue'])} in total:\n" + _bullets(
            f"{c['name']}: {inr(c['overdue'])}, {c['days_overdue']} days" for c in late
        )

    if has("total", "kitna", "kul", "how much", "outstanding"):
        return (f"Customers owe you {inr(t['outstanding'])} in total. {inr(t['overdue'])} of that is late, "
                f"and {inr(t['due_this_week'])} is due in the next 7 days.")

    return ("In offline mode I can answer simple questions like: \"Who owes the most?\", "
            "\"Who is late?\", \"What's due this week?\", \"How much is owed in total?\" or a customer's name. "
            "Add an API key to ask anything.")
