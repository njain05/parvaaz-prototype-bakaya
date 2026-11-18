// Today: the home screen. One line of totals, then who to contact and why (PLAN.md §Today, §Today rules).

import { $, api, esc, fmtDate, lakh } from "./lib.js";
import { openReminder } from "./reminder.js";

const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

// "2026-11-18" -> "Wednesday, 18 November"
function longDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return `${DAYS[new Date(y, m - 1, d).getDay()]}, ${d} ${MONTHS[m - 1]}`;
}

function rowHtml(r, late) {
  return `
    <li class="row" data-customer="${r.customer_id}" tabindex="0" role="link" aria-label="${esc(r.name)}: open customer">
      <div class="row-name">${esc(r.name)}</div>
      <div class="row-right">
        <div class="amount ${late ? "late" : ""}">${lakh(r.amount)}<span class="amount-label">${late ? "late" : "due " + fmtDate(r.due_date)}</span></div>
      </div>
      <div class="row-sub">${esc(r.city)}</div>
      <p class="row-why">${esc(r.why)}</p>
      ${r.remind_order_id ? `<div class="row-actions"><button class="btn" type="button" data-remind="${r.customer_id}" data-order="${r.remind_order_id}">Send reminder</button></div>` : ""}
    </li>`;
}

function groupHtml(title, rows, late) {
  if (!rows.length) return "";
  return `
    <section aria-label="${title}">
      <div class="section-head"><h2>${title}</h2><span class="count">${rows.length} ${rows.length === 1 ? "customer" : "customers"}</span></div>
      <ul class="rows today-rows">${rows.map((r) => rowHtml(r, late)).join("")}</ul>
    </section>`;
}

export async function render(el) {
  if (!el.dataset.ready) {
    el.innerHTML = `
      <div class="page-head" id="today-head"><h1 class="page-title">Today</h1></div>
      <div id="today-list"><p class="loading">Loading…</p></div>`;
    wire(el);
    el.dataset.ready = "1";
  }

  let data;
  try {
    data = await api("/api/today");
  } catch (e) {
    $("#today-list", el).innerHTML = `<p class="error">${esc(e.message)}</p>`;
    return;
  }

  const t = data.totals;
  $("#today-head", el).innerHTML = `
    <span class="eyebrow">${longDate(data.today)}</span>
    <h1 class="page-title">Today</h1>
    <p class="totals"><strong>${lakh(t.owed)}</strong> owed to you · <strong class="late">${lakh(t.late)}</strong> late</p>`;

  $("#today-list", el).innerHTML = data.late.length || data.coming_up.length
    ? groupHtml("Late", data.late, true) + groupHtml("Coming up", data.coming_up, false)
    : `<p class="today-empty">Nobody to chase today. Everyone has paid, been reminded, or promised a date.</p>`;
}

// One set of listeners on the screen's element; rows are redrawn after each reminder.
function wire(el) {
  const open = (row) => { location.hash = `#/customers/${row.dataset.customer}`; };
  el.addEventListener("click", (e) => {
    const remind = e.target.closest("[data-remind]");
    if (remind) {
      openReminder(Number(remind.dataset.remind), Number(remind.dataset.order), { onSent: () => render(el) });
      return;
    }
    const row = e.target.closest("[data-customer]");
    if (row) open(row);
  });
  el.addEventListener("keydown", (e) => {
    const row = e.target.closest?.("[data-customer]");
    if (row && e.target === row && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      open(row);
    }
  });
}
