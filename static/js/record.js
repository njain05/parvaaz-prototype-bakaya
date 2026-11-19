// Record payment and Note a promise: two sheets opened from the customer page (PLAN.md §Customer page,
// §Today rules 4–5). `customer` is the GET /api/customers/<id> response.

import { $, addDays, esc, fmtDate, inr, openSheet, closeSheet, postJSON, toast } from "./lib.js";

const MODES = ["NEFT", "RTGS", "UPI", "Cheque", "Cash"];

const pad = (n) => String(n).padStart(2, "0");
const todayISO = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };

// "5,10,000" or "₹5,10,000" -> 510000; empty -> null (the server then asks for the amount)
const parseAmount = (s) => { const v = String(s).replace(/[₹,\s]/g, ""); return v ? Number(v) : null; };

// The amount the owner most likely received: the sale's late amount, else its next instalment, else its balance.
function likelyAmount(sale) {
  if (sale.overdue > 0.5) return sale.overdue;
  const next = sale.milestones.find((m) => m.status !== "paid" && m.unpaid > 0.5);
  return next ? next.unpaid : sale.balance;
}

// Unpaid instalments due between today and 7 days from now, across the customer's sales.
export function dueSoon(customer) {
  const today = todayISO(), weekEnd = addDays(today, 7);
  return customer.sales.flatMap((s) => s.milestones)
    .filter((m) => m.status === "upcoming" && m.unpaid > 0.5 && m.due_date >= today && m.due_date <= weekEnd)
    .reduce((sum, m) => sum + m.unpaid, 0);
}

function sheetHtml(id, title, sub, fields, saveLabel) {
  return `
    <form class="sheet-body record" id="${id}" novalidate>
      <div class="sheet-grip" aria-hidden="true"></div>
      <div class="sheet-head">
        <div>
          <h2 class="sheet-title" id="sheet-title">${title}</h2>
          <p class="sheet-sub">${sub}</p>
        </div>
        <button class="btn btn-link sheet-close" type="button" data-close>Close</button>
      </div>
      ${fields}
      <p class="error record-error" role="alert" hidden></p>
      <div class="sheet-foot">
        <button class="btn" type="button" data-close>Cancel</button>
        <button class="btn btn-primary" type="submit">${saveLabel}</button>
      </div>
    </form>`;
}

// Shared submit handling: block double taps, show the server's error inside the sheet.
function onSave(form, save) {
  const error = $(".record-error", form);
  const button = $("[type=submit]", form);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (button.disabled) return;
    error.hidden = true;
    button.disabled = true;
    try {
      await save();
    } catch (err) {
      if (!form.isConnected) return;
      error.textContent = err.message;
      error.hidden = false;
    } finally {
      button.disabled = false;
    }
  });
}

export function openRecordPayment(customer, { onSaved } = {}) {
  const unpaid = customer.sales.filter((s) => s.balance > 0.5);
  if (!unpaid.length) return;
  let sale = unpaid.find((s) => s.id === customer.remind_order_id) || unpaid[0];
  let mode = MODES[0];

  const salePicker = unpaid.length === 1
    ? `<p class="record-for">For: ${esc(sale.machine)}</p>`
    : `<fieldset class="field record-sales">
        <legend>Which sale</legend>
        ${unpaid.map((s) => `
          <label class="record-sale">
            <input type="radio" name="sale" value="${s.id}" ${s.id === sale.id ? "checked" : ""}>
            <span class="record-sale-name">${esc(s.machine)}</span>
            <span class="record-sale-bal ${s.overdue > 0.5 ? "late" : ""}">${inr(s.balance)} left${s.overdue > 0.5 ? ` · ${inr(s.overdue)} late` : ""}</span>
          </label>`).join("")}
      </fieldset>`;

  const sheet = openSheet(sheetHtml("record-form", "Record payment", esc(customer.name), `
    ${salePicker}
    <div class="record-pair">
      <div class="field">
        <label for="pay-amount">Amount (₹)</label>
        <input id="pay-amount" class="input num" inputmode="numeric" autocomplete="off" value="${Math.round(likelyAmount(sale))}">
      </div>
      <div class="field">
        <label for="pay-date">Date</label>
        <input id="pay-date" class="input" type="date" value="${todayISO()}" max="${todayISO()}">
      </div>
    </div>
    <div class="field">
      <label id="mode-label">Mode</label>
      <div class="segmented" role="group" aria-labelledby="mode-label">
        ${MODES.map((m) => `<button type="button" data-mode="${m}" aria-pressed="${m === mode}">${m}</button>`).join("")}
      </div>
    </div>
    <div class="field">
      <label for="pay-note">Note <span class="record-optional">(optional)</span></label>
      <input id="pay-note" class="input" autocomplete="off" placeholder="Cheque no., UTR…">
    </div>`, "Save payment"));

  const form = $("#record-form", sheet);
  const amount = $("#pay-amount", sheet);
  sheet.querySelectorAll("input[name=sale]").forEach((r) => r.addEventListener("change", () => {
    sale = unpaid.find((s) => s.id === Number(r.value));
    amount.value = Math.round(likelyAmount(sale));
  }));
  sheet.querySelectorAll("[data-mode]").forEach((b) => b.addEventListener("click", () => {
    mode = b.dataset.mode;
    sheet.querySelectorAll("[data-mode]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  }));

  onSave(form, async () => {
    const value = parseAmount(amount.value);
    await postJSON(`/api/orders/${sale.id}/payments`, {
      amount: value, date: $("#pay-date", sheet).value, mode, note: $("#pay-note", sheet).value.trim(),
    });
    closeSheet();
    onSaved?.();
    toast(`${inr(value)} received from ${customer.name}`);
  });
}

export function openPromise(customer, { onSaved } = {}) {
  const today = todayISO();
  const amountGuess = customer.late > 0.5 ? customer.late : dueSoon(customer);
  const sheet = openSheet(sheetHtml("promise-form", "Note a promise", `What ${esc(customer.contact_person || customer.name)} said they'll pay`, `
    <div class="record-pair">
      <div class="field">
        <label for="promise-amount">Amount (₹)</label>
        <input id="promise-amount" class="input num" inputmode="numeric" autocomplete="off" value="${amountGuess > 0.5 ? Math.round(amountGuess) : ""}">
      </div>
      <div class="field">
        <label for="promise-date">Pay by</label>
        <input id="promise-date" class="input" type="date" value="${addDays(today, 7)}" min="${today}">
      </div>
    </div>
    <div class="field">
      <label for="promise-note">Note <span class="record-optional">(optional)</span></label>
      <input id="promise-note" class="input" autocomplete="off" placeholder="What they said">
    </div>`, "Save promise"));

  const form = $("#promise-form", sheet);
  onSave(form, async () => {
    const date = $("#promise-date", sheet).value;
    await postJSON(`/api/customers/${customer.id}/contacts`, {
      kind: "promise",
      promised_amount: parseAmount($("#promise-amount", sheet).value),
      promised_date: date,
      note: $("#promise-note", sheet).value.trim(),
    });
    closeSheet();
    onSaved?.();
    toast(`Promise noted. ${customer.name} is off Today until ${fmtDate(date)}.`);
  });
}
