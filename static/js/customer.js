// Customer page: how to reach them, what they owe, their machines and instalments, and one history of
// payments, reminders and promises (PLAN.md §Customer page).

import { $, api, daysBetween, esc, fmtDate, inr, lakh, whatsappUrl } from "./lib.js";
import { openReminder } from "./reminder.js";
import { dueSoon, openPromise, openRecordPayment } from "./record.js";

const LANG_NAMES = { hinglish: "Hinglish", hindi: "Hindi", punjabi: "Punjabi", english: "English" };

// Back goes to the previous screen only when there is one inside the app; a page opened directly goes to Customers.
let cameFromApp = false;
window.addEventListener("hashchange", () => { cameFromApp = true; });

const pad = (n) => String(n).padStart(2, "0");
const todayISO = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };

function habitWords(c) {
  if (c.habit === "new" || c.avg_days_late == null) return "New customer";
  if (c.habit === "on_time") return "Usually pays on time";
  return `Usually pays about ${c.avg_days_late} days late`;
}

function headHtml(c) {
  const tel = String(c.phone || "").replace(/\s/g, "");
  const meta = [c.contact_person, c.city].filter(Boolean).map(esc).join(" · ");
  return `
    <div class="cust-head">
      <h1 class="page-title">${esc(c.name)}</h1>
      ${meta ? `<p class="cust-meta">${meta}${c.phone ? ` · <span class="num">${esc(c.phone)}</span>` : ""}</p>` : ""}
      ${c.phone ? `
        <div class="btn-row">
          <a class="btn" href="tel:${esc(tel)}">Call</a>
          <a class="btn" href="${esc(whatsappUrl(c.phone, ""))}" target="_blank" rel="noopener">WhatsApp</a>
        </div>` : ""}
    </div>`;
}

function summaryHtml(c) {
  const owes = c.owed > 0.5
    ? `Owes ${lakh(c.owed)}${c.late > 0.5 ? `<span class="sep">·</span><span class="late">${lakh(c.late)} late (${c.days_late} days)</span>` : ""}`
    : "Paid up";
  const p = c.promise;
  const promise = p && (p.state === "open" || p.state === "broken")
    ? `<p class="cust-promise">Promised ${lakh(p.amount)} by ${fmtDate(p.promised_date)}${p.state === "broken" ? ` · <span class="late">Not received</span>` : ""}</p>`
    : "";
  return `
    <div class="cust-summary">
      <p class="cust-owes">${owes}</p>
      <p class="cust-habit">${habitWords(c)}</p>
      ${promise}
    </div>`;
}

// One instalment: label and amount, then its state in words.
function instHtml(m, today) {
  const due = `Due ${fmtDate(m.due_date)}`;
  if (m.status === "paid") {
    return `<li class="is-paid"><span class="inst-mark" aria-label="Paid">✓</span><span class="inst-label">${esc(m.label)}</span>
      <span class="inst-amt">${inr(m.amount)}</span><span class="inst-note">${due} · Paid ${fmtDate(m.paid_on)}</span></li>`;
  }
  const left = m.partly_paid ? `${inr(m.unpaid)} left · ` : "";
  if (m.status === "overdue") {
    const days = daysBetween(m.due_date, today);
    return `<li class="is-late"><span class="inst-mark" aria-hidden="true">!</span><span class="inst-label">${esc(m.label)}</span>
      <span class="inst-amt">${inr(m.amount)}</span><span class="inst-note">${due} · ${left}${days} ${days === 1 ? "day" : "days"} late</span></li>`;
  }
  return `<li class="is-upcoming"><span class="inst-mark" aria-hidden="true">·</span><span class="inst-label">${esc(m.label)}</span>
    <span class="inst-amt">${inr(m.amount)}</span><span class="inst-note">${left}${due}</span></li>`;
}

function saleHtml(o, today) {
  return `
    <div class="sale">
      <div class="sale-head"><span class="sale-name">${esc(o.machine)}</span><span class="num">${inr(o.total)}</span></div>
      <div class="sale-meta">Sold ${fmtDate(o.order_date, true)} · ${o.balance <= 0.5 ? "Paid in full" : `Paid ${inr(o.paid)} of ${inr(o.total)}`}</div>
      <ul class="inst">${o.milestones.map((m) => instHtml(m, today)).join("")}</ul>
    </div>`;
}

function historyHtml(h, c) {
  let what, detail, late = false;
  if (h.kind === "payment") {
    what = `Paid ${inr(h.amount)}${h.mode ? ` · ${h.mode}` : ""}`;
    detail = h.machine;
  } else if (h.kind === "reminder") {
    what = h.language ? `Reminder sent (${LANG_NAMES[h.language] || h.language})` : "Reminder sent";
    detail = h.machine;
  } else {
    late = c.promise?.contact_id === h.contact_id && c.promise.state === "broken";
    what = `Promised ${inr(h.amount)} by ${fmtDate(h.promised_date)}`;
    detail = [late ? "Not received" : "", h.note].filter(Boolean).join(" · ");
  }
  return `
    <li><time datetime="${h.date}">${fmtDate(h.date)}</time>
      <div><div class="what${late ? " late" : ""}">${esc(what)}</div>${detail ? `<div class="detail">${esc(detail)}</div>` : ""}</div></li>`;
}

export async function render(el, id) {
  el.innerHTML = `
    <a class="back" href="#/customers" id="cust-back">‹ Back</a>
    <div id="cust-body"><p class="loading">Loading…</p></div>`;
  $("#cust-back", el).addEventListener("click", (e) => {
    if (!cameFromApp) return; // follow the link to Customers
    e.preventDefault();
    history.back();
  });
  let current = null; // the customer as last drawn, for the Record payment and Note a promise sheets
  const redraw = async () => { current = await draw(el, id); };
  el.addEventListener("click", (e) => {
    const remind = e.target.closest("[data-remind]");
    if (remind) openReminder(id, Number(remind.dataset.remind), { onSent: redraw });
    if (current && e.target.closest("[data-record]")) openRecordPayment(current, { onSaved: redraw });
    if (current && e.target.closest("[data-promise]")) openPromise(current, { onSaved: redraw });
  });
  await redraw();
}

// Send reminder, then Record payment (anything owed), then Note a promise (late, or due in the next 7 days).
function actionsHtml(c) {
  return [
    c.remind_order_id ? `<button class="btn btn-primary" type="button" data-remind="${c.remind_order_id}">Send reminder</button>` : "",
    c.owed > 0.5 ? `<button class="btn" type="button" data-record>Record payment</button>` : "",
    c.late > 0.5 || dueSoon(c) > 0.5 ? `<button class="btn" type="button" data-promise>Note a promise</button>` : "",
  ].join("");
}

async function draw(el, id) {
  const body = $("#cust-body", el);
  let c;
  try {
    c = await api(`/api/customers/${id}`);
  } catch (e) {
    body.innerHTML = `<p class="error">${esc(e.message)}</p><p class="coming-soon"><a href="#/customers">See all customers</a></p>`;
    return null;
  }
  const today = todayISO();
  const history = c.history.map((h) => historyHtml(h, c)).join("");
  body.innerHTML = `
    ${headHtml(c)}
    ${summaryHtml(c)}
    <div class="btn-row cust-actions" id="cust-actions">${actionsHtml(c)}</div>
    <section aria-label="Machines">
      <div class="section-head"><h2>Machines</h2><span class="count">${c.sales.length} ${c.sales.length === 1 ? "sale" : "sales"}</span></div>
      ${c.sales.map((o) => saleHtml(o, today)).join("") || `<p class="today-empty">No sales yet.</p>`}
    </section>
    <section aria-label="History">
      <div class="section-head"><h2>History</h2></div>
      ${history ? `<ul class="history">${history}</ul>` : `<p class="today-empty">No payments or reminders yet.</p>`}
    </section>`;
  return c;
}
