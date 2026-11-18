// Send reminder sheet: pick a language, check the draft, send it on WhatsApp.
// Sending logs a reminder in the contact log, with Undo in the toast (PLAN.md §Send reminder, Assumed 2).

import { $, api, del, esc, fmtDate, inr, openSheet, closeSheet, postJSON, store, toast, whatsappUrl } from "./lib.js";

const LANGS = [["hinglish", "Hinglish", "en"], ["hindi", "हिंदी", "hi"], ["punjabi", "ਪੰਜਾਬੀ", "pa"], ["english", "English", "en"]];

function savedLang() {
  const lang = store("lang");
  return LANGS.some(([k]) => k === lang) ? lang : "hinglish";
}

// "₹6,95,000 late, 60 days · Raising Machine" or "₹9,60,000 due 18 Nov · Raising Machine"
function aboutLine(sale) {
  if (!sale) return "";
  if (sale.overdue > 0.5) {
    return `<span class="late">${inr(sale.overdue)} late, ${sale.days_overdue} days</span> · ${esc(sale.machine)}`;
  }
  const due = sale.next_due ? `${inr(sale.next_due.amount)} due ${fmtDate(sale.next_due.due_date)}` : inr(sale.balance);
  return `${due} · ${esc(sale.machine)}`;
}

export function openReminder(customerId, orderId, { onSent } = {}) {
  let lang = savedLang();
  let customer = null;
  let phone = "";
  let draftToken = 0;
  let saleProblem = false; // the sale isn't this customer's, or the customer couldn't be loaded

  const sheet = openSheet(`
    <form class="sheet-body reminder" id="remind-form" novalidate>
      <div class="sheet-grip" aria-hidden="true"></div>
      <div class="sheet-head">
        <div>
          <h2 class="sheet-title" id="sheet-title">Reminder</h2>
          <p class="sheet-sub" id="remind-about">Loading…</p>
        </div>
        <button class="btn btn-link sheet-close" type="button" data-close>Close</button>
      </div>
      <div class="field">
        <label id="lang-label">Language</label>
        <div class="segmented" role="group" aria-labelledby="lang-label">
          ${LANGS.map(([k, label, code]) => `<button type="button" data-lang="${k}" lang="${code}" aria-pressed="${k === lang}">${label}</button>`).join("")}
        </div>
      </div>
      <div class="field">
        <label for="remind-text">Message<span id="remind-to"></span></label>
        <textarea id="remind-text" class="textarea" placeholder="Writing…"></textarea>
        <div class="reminder-source">
          <p id="remind-source" aria-live="polite"></p>
          <button class="btn btn-link" type="button" id="remind-rewrite">Rewrite</button>
        </div>
      </div>
      <div class="sheet-foot">
        <button class="btn" type="button" data-close>Cancel</button>
        <button class="btn btn-primary" type="submit" id="remind-send">Send on WhatsApp</button>
      </div>
    </form>`);

  const form = $("#remind-form", sheet);
  const text = $("#remind-text", sheet);
  const source = $("#remind-source", sheet);
  const send = $("#remind-send", sheet);
  // The sheet may be closed or reused for another customer while a request is running.
  const stillOpen = () => form.isConnected && sheet.open;
  const updateSend = () => { send.disabled = saleProblem || text.readOnly || !text.value.trim(); };
  const showProblem = (message) => {
    saleProblem = true;
    $("#remind-about", sheet).innerHTML = `<span class="error">${esc(message)}</span>`;
    updateSend();
  };

  // Header: who it's to and which sale it's about.
  api(`/api/customers/${customerId}`).then((c) => {
    if (!stillOpen()) return;
    customer = c;
    phone ||= c.phone;
    $("#sheet-title", sheet).textContent = `Reminder to ${c.name}`;
    if (c.contact_person) $("#remind-to", sheet).textContent = ` to ${c.contact_person}`;
    const sale = c.sales.find((s) => s.id === orderId);
    if (sale) $("#remind-about", sheet).innerHTML = aboutLine(sale);
    else showProblem("That sale isn't this customer's.");
  }).catch((e) => {
    if (stillOpen()) showProblem(e.message);
  });

  async function draft() {
    const token = ++draftToken;
    text.value = "";
    text.readOnly = true;
    text.placeholder = "Writing…";
    source.textContent = "";
    source.className = "";
    updateSend();
    try {
      const r = await postJSON("/api/ai/reminder", { order_id: orderId, language: lang });
      if (!stillOpen() || token !== draftToken) return;
      phone = r.phone || phone;
      text.value = r.message;
      source.textContent = (r.source === "ai" ? "Written by AI. Check it before sending." : "Written from a template.")
        + (r.note ? ` ${r.note}` : "");
    } catch (e) {
      if (!stillOpen() || token !== draftToken) return;
      text.placeholder = "Type the message, or tap Rewrite to try again.";
      source.textContent = e.message;
      source.className = "error";
    } finally {
      if (stillOpen() && token === draftToken) {
        text.readOnly = false;
        text.setSelectionRange(0, 0);
        text.scrollTop = 0;
        updateSend();
      }
    }
  }

  sheet.querySelectorAll("[data-lang]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.lang === lang) return;
    lang = b.dataset.lang;
    store("lang", lang);
    sheet.querySelectorAll("[data-lang]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    draft();
  }));
  $("#remind-rewrite", sheet).addEventListener("click", draft);
  text.addEventListener("input", updateSend);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = text.value.trim();
    if (!message || text.readOnly || saleProblem) return;
    // Open WhatsApp straight from the tap, before any await, so the browser doesn't block the new tab.
    window.open(whatsappUrl(phone, message), "_blank");
    const name = customer?.name || "the customer";
    closeSheet();
    let logged;
    try {
      logged = await postJSON(`/api/customers/${customerId}/contacts`, { kind: "reminder", order_id: orderId, language: lang });
    } catch (err) {
      toast(`Sent, but couldn't save it in the history: ${err.message}`);
      return;
    }
    onSent?.();
    toast(`Reminder sent to ${name}`, {
      action: {
        label: "Undo",
        onClick: async () => {
          try {
            await del(`/api/contacts/${logged.id}`);
          } catch (err) {
            toast(err.message);
            return;
          }
          onSent?.();
          toast("Reminder removed");
        },
      },
    });
  });

  draft();
}
