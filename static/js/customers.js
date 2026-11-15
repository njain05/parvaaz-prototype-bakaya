// Customers: everyone A–Z, with a search by name or city and what each one owes (PLAN.md Assumed 6).

import { $, api, esc, lakh } from "./lib.js";

function rowHtml(c) {
  const owes = c.outstanding > 0.5, late = c.overdue > 0.5;
  return `
    <li><a class="row" href="#/customers/${c.id}">
      <div><div class="row-name">${esc(c.name)}</div><div class="row-sub">${esc(c.city)}</div></div>
      <div class="row-right"><div class="amount ${late ? "late" : ""}">${owes ? lakh(c.outstanding) : "Paid up"}
        <span class="amount-label">${late ? lakh(c.overdue) + " late" : owes ? "owed" : ""}</span></div></div>
    </a></li>`;
}

export async function render(el) {
  el.innerHTML = `
    <div class="page-head"><h1 class="page-title">Customers</h1></div>
    <div class="field customers-search">
      <label for="cust-search" class="visually-hidden">Search customers</label>
      <input id="cust-search" class="input" type="search" placeholder="Search by name or city" autocomplete="off">
    </div>
    <ul class="rows customers" id="cust-list"><li class="loading">Loading…</li></ul>`;

  let list;
  try {
    const book = await api("/api/book");
    list = [...book.customers].sort((a, b) => a.name.localeCompare(b.name));
  } catch (e) {
    $("#cust-list", el).innerHTML = `<li class="error">${esc(e.message)}</li>`;
    return;
  }

  const search = $("#cust-search", el);
  const draw = () => {
    const q = search.value.trim().toLowerCase();
    const rows = list.filter((c) => !q || `${c.name} ${c.city}`.toLowerCase().includes(q));
    $("#cust-list", el).innerHTML = rows.map(rowHtml).join("") || `<li class="empty">No customer matches that.</li>`;
  };
  search.addEventListener("input", draw);
  draw();
}
