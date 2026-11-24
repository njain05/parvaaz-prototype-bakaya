// Add sale sheet: customer, machine, price and dates, with the standard payment plan filled in.
// Scanning a bill fills in the same form (PLAN.md §Add sale).

import { $, addDays, api, closeSheet, esc, fmtDate, getStatus, inr, openSheet, postJSON, toast } from "./lib.js";

const PLANS = [
  ["30-60-10", "30/60/10", "30% advance · 60% before dispatch · 10% after installation"],
  ["50-50", "50/50", "50% advance · 50% before dispatch"],
  ["100", "Full on delivery", "Full payment on delivery"],
];

const pad = (n) => String(n).padStart(2, "0");
const todayISO = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };
const isISO = (s) => /^\d{4}-\d{2}-\d{2}$/.test(s || "");

// "7,20,000" or "₹7,20,000" -> 720000; empty or not a number -> null
function parseAmount(s) {
  const v = String(s ?? "").replace(/[₹,\s]/g, "");
  if (!v) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

export function planMilestones(plan, total, orderDate, dispatchDate) {
  if (plan === "100") return [{ label: "Full payment", amount: total, due_date: dispatchDate }];
  if (plan === "50-50") {
    const a = Math.round(total * 0.5);
    return [{ label: "Advance", amount: a, due_date: orderDate }, { label: "Before dispatch", amount: total - a, due_date: dispatchDate }];
  }
  const a = Math.round(total * 0.3), d = Math.round(total * 0.6);
  return [
    { label: "Advance", amount: a, due_date: orderDate },
    { label: "Before dispatch", amount: d, due_date: dispatchDate },
    { label: "After installation", amount: total - a - d, due_date: addDays(dispatchDate, 30) },
  ];
}

export function openAddSale(prefill = {}) {
  let plan = PLANS[0][0];
  let customers = [];   // [{id, name, city}] from /api/book
  let chosen = null;    // the existing customer picked from the list
  let isNew = false;    // "+ New customer" fields shown
  const today = todayISO();

  const sheet = openSheet(`
    <form class="sheet-body add-sale" id="sale-form" novalidate>
      <div class="sheet-grip" aria-hidden="true"></div>
      <div class="sheet-head">
        <h2 class="sheet-title" id="sheet-title">Add sale</h2>
        <button class="btn btn-link sheet-close" type="button" data-close>Close</button>
      </div>

      <div class="sale-scan" id="sale-scan">
        <button class="btn" type="button" id="scan-btn">Scan a bill</button>
        <input type="file" id="scan-file" accept="image/jpeg,image/png,image/webp" capture="environment" hidden>
        <p class="sale-scan-msg" id="scan-msg" aria-live="polite"></p>
      </div>

      <div class="field" id="cust-pick">
        <label for="sale-cust">Customer</label>
        <input id="sale-cust" class="input" type="search" autocomplete="off" placeholder="Search by name or city"
          aria-expanded="false" aria-controls="sale-cust-list">
        <ul class="sale-cust-list" id="sale-cust-list" aria-label="Matching customers" hidden></ul>
      </div>
      <fieldset class="sale-new" id="sale-new" hidden>
        <legend>New customer <button class="btn btn-link" type="button" id="sale-existing">Choose existing</button></legend>
        <div class="sale-grid">
          <div class="field"><label for="nc-name">Firm name</label><input id="nc-name" class="input" autocomplete="off"></div>
          <div class="field"><label for="nc-person">Contact person</label><input id="nc-person" class="input" autocomplete="off"></div>
          <div class="field"><label for="nc-phone">Phone</label><input id="nc-phone" class="input" type="tel" autocomplete="off"></div>
          <div class="field"><label for="nc-city">City</label><input id="nc-city" class="input" autocomplete="off"></div>
        </div>
      </fieldset>

      <div class="field">
        <label for="sale-machine">Machine</label>
        <input id="sale-machine" class="input" autocomplete="off" placeholder="e.g. Raising Machine, 24 roller">
      </div>
      <div class="field">
        <label for="sale-price">Price (₹)</label>
        <input id="sale-price" class="input num" inputmode="numeric" autocomplete="off" placeholder="e.g. 7,20,000">
        <p class="sale-plan-line"><span id="plan-line">${PLANS[0][2]}</span>
          <button class="btn btn-link" type="button" id="plan-toggle" aria-expanded="false" aria-controls="plan-box">Change plan</button></p>
      </div>
      <div class="sale-plan" id="plan-box" hidden>
        <div class="segmented" role="group" aria-label="Payment plan">
          ${PLANS.map(([k, short]) => `<button type="button" data-plan="${k}" aria-pressed="${k === plan}">${short}</button>`).join("")}
        </div>
        <div id="plan-preview"></div>
      </div>
      <div class="sale-grid">
        <div class="field"><label for="sale-date">Sale date</label><input id="sale-date" class="input" type="date" value="${today}"></div>
        <div class="field"><label for="sale-dispatch">Expected dispatch</label><input id="sale-dispatch" class="input" type="date" value="${addDays(today, 45)}"></div>
      </div>
      <div class="field">
        <label for="sale-advance">Advance received now (₹)</label>
        <input id="sale-advance" class="input num" inputmode="numeric" autocomplete="off" value="0">
      </div>

      <p class="error sale-error" id="sale-error" role="alert" hidden></p>
      <div class="sheet-foot">
        <button class="btn" type="button" data-close>Cancel</button>
        <button class="btn btn-primary" type="submit" id="sale-save">Save sale</button>
      </div>
    </form>`);

  const form = $("#sale-form", sheet);
  const q = (sel) => $(sel, sheet);
  const custInput = q("#sale-cust"), list = q("#sale-cust-list");
  const stillOpen = () => form.isConnected && sheet.open;

  // ---------- customer: search an existing one, or add a new one ----------
  function showList(open) {
    list.hidden = !open;
    custInput.setAttribute("aria-expanded", String(open));
  }
  function drawList() {
    const text = custInput.value.trim().toLowerCase();
    const matches = customers.filter((c) => !text || `${c.name} ${c.city}`.toLowerCase().includes(text)).slice(0, 6);
    list.innerHTML = matches.map((c) => `
      <li><button type="button" data-cust="${c.id}">
        <span class="sale-cust-name">${esc(c.name)}</span><span class="sale-cust-city">${esc(c.city)}</span></button></li>`).join("")
      + `<li><button type="button" data-new-cust class="sale-cust-add">+ New customer${custInput.value.trim() ? `: ${esc(custInput.value.trim())}` : ""}</button></li>`;
    showList(true);
  }
  function choose(c) {
    chosen = c;
    custInput.value = c.name;
    custInput.classList.add("is-chosen");
    showList(false);
  }
  function setNew(on, name = "") {
    isNew = on;
    q("#cust-pick").hidden = on;
    q("#sale-new").hidden = !on;
    showList(false);
    if (on) {
      chosen = null;
      if (name) q("#nc-name").value = name;
      q("#nc-name").focus();
    } else {
      custInput.focus();
    }
  }

  custInput.addEventListener("input", () => {
    chosen = null;
    custInput.classList.remove("is-chosen");
    drawList();
  });
  custInput.addEventListener("focus", () => { if (!chosen) drawList(); });
  custInput.addEventListener("keydown", (e) => { if (e.key === "Escape" && !list.hidden) { e.preventDefault(); showList(false); } });
  list.addEventListener("click", (e) => {
    const pick = e.target.closest("[data-cust]");
    if (pick) choose(customers.find((c) => c.id === Number(pick.dataset.cust)));
    else if (e.target.closest("[data-new-cust]")) setNew(true, custInput.value.trim());
  });
  list.addEventListener("mousedown", (e) => e.preventDefault()); // keep focus in the search box while picking
  // Close the list when focus leaves the customer field.
  q("#cust-pick").addEventListener("focusout", (e) => {
    if (!q("#cust-pick").contains(e.relatedTarget)) showList(false);
  });
  q("#sale-existing").addEventListener("click", () => setNew(false));

  // ---------- plan line, Change plan, preview ----------
  function preview() {
    const total = parseAmount(q("#sale-price").value);
    const box = q("#plan-preview");
    if (!total || total <= 0) {
      box.innerHTML = `<p class="sale-plan-empty">Enter the price to see the instalments.</p>`;
      return;
    }
    const ms = planMilestones(plan, total, q("#sale-date").value, q("#sale-dispatch").value);
    box.innerHTML = `<table class="sale-plan-table"><tbody>${ms.map((m) => `
      <tr><td>${esc(m.label)}</td><td>${m.due_date ? fmtDate(m.due_date) : "—"}</td><td class="num">${inr(m.amount)}</td></tr>`).join("")}</tbody></table>`;
  }
  q("#plan-toggle").addEventListener("click", () => {
    const box = q("#plan-box");
    box.hidden = !box.hidden;
    q("#plan-toggle").setAttribute("aria-expanded", String(!box.hidden));
    q("#plan-toggle").textContent = box.hidden ? "Change plan" : "Hide plan";
    preview();
  });
  sheet.querySelectorAll("[data-plan]").forEach((b) => b.addEventListener("click", () => {
    plan = b.dataset.plan;
    sheet.querySelectorAll("[data-plan]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    q("#plan-line").textContent = PLANS.find(([k]) => k === plan)[2];
    preview();
  }));
  // Moving the order date moves the dispatch date with it, keeping the gap.
  let lastOrderDate = today;
  q("#sale-date").addEventListener("change", () => {
    const d = q("#sale-date").value, dispatch = q("#sale-dispatch").value;
    if (isISO(d) && isISO(lastOrderDate) && isISO(dispatch)) {
      const gap = Math.round((Date.parse(dispatch) - Date.parse(lastOrderDate)) / 86400000);
      q("#sale-dispatch").value = addDays(d, gap);
    }
    lastOrderDate = d;
  });
  ["#sale-price", "#sale-date", "#sale-dispatch"].forEach((s) => q(s).addEventListener("input", preview));
  ["#sale-date", "#sale-dispatch"].forEach((s) => q(s).addEventListener("change", preview));

  // ---------- fill the form from a scanned bill ----------
  function fill(r) {
    const name = (r.customer_name || "").trim();
    if (name) {
      const match = customers.find((c) => c.name.toLowerCase() === name.toLowerCase());
      if (match) {
        if (isNew) setNew(false);
        choose(match);
      } else {
        setNew(true, name);
        if (r.contact_person) q("#nc-person").value = r.contact_person;
        if (r.phone) q("#nc-phone").value = r.phone;
        if (r.city) q("#nc-city").value = r.city;
      }
    }
    if (r.item) q("#sale-machine").value = r.item;
    if (r.total_amount) q("#sale-price").value = Math.round(r.total_amount);
    if (isISO(r.invoice_date)) {
      q("#sale-date").value = r.invoice_date;
      q("#sale-dispatch").value = addDays(r.invoice_date, 45);
      lastOrderDate = r.invoice_date;
    }
    if (r.amount_paid) q("#sale-advance").value = Math.round(r.amount_paid);
    preview();
  }

  const scanMsg = q("#scan-msg"), scanBtn = q("#scan-btn"), scanFile = q("#scan-file");
  function scanNote(text, error = false) {
    scanMsg.textContent = text;
    scanMsg.className = "sale-scan-msg" + (error ? " error" : "");
  }
  scanBtn.addEventListener("click", () => scanFile.click());
  scanFile.addEventListener("change", async () => {
    const file = scanFile.files[0];
    if (!file) return;
    const body = new FormData();
    body.append("image", file);
    scanBtn.disabled = true;
    scanBtn.textContent = "Reading the bill…";
    scanNote("");
    try {
      const r = await api("/api/ai/scan", { method: "POST", body });
      if (!stillOpen()) return;
      fill(r);
      scanNote("Filled in from the bill. Check every field before saving.");
    } catch (e) {
      if (stillOpen()) scanNote(e.message, true);
    } finally {
      scanBtn.disabled = false;
      scanBtn.textContent = "Scan a bill";
      scanFile.value = "";
    }
  });
  getStatus().then((s) => {
    if (!stillOpen() || s.ai_enabled) return;
    scanBtn.remove();
    scanNote("Scanning bills needs the AI (add an API key).");
  }).catch(() => {});

  // ---------- save ----------
  const error = q("#sale-error"), save = q("#sale-save");
  const showError = (text) => { error.textContent = text; error.hidden = false; };
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (save.disabled) return;
    error.hidden = true;

    let customer;
    if (isNew) {
      customer = { new_customer: { name: q("#nc-name").value.trim(), contact_person: q("#nc-person").value.trim(),
        phone: q("#nc-phone").value.trim(), city: q("#nc-city").value.trim() } };
    } else {
      // A typed name that matches one customer exactly counts as choosing them.
      const typed = custInput.value.trim().toLowerCase();
      const c = chosen || customers.find((x) => x.name.toLowerCase() === typed);
      if (!c) {
        showError(typed ? "Choose the customer from the list, or add them as a new customer." : "Choose a customer.");
        custInput.focus();
        return;
      }
      customer = { customer_id: c.id };
    }

    const total = parseAmount(q("#sale-price").value);
    const orderDate = q("#sale-date").value, dispatch = q("#sale-dispatch").value;
    if (!isISO(dispatch)) { showError("Enter the expected dispatch date."); return; }
    const advance = parseAmount(q("#sale-advance").value);
    save.disabled = true;
    try {
      const r = await postJSON("/api/orders", {
        ...customer,
        machine: q("#sale-machine").value.trim(),
        total,
        order_date: orderDate,
        milestones: total > 0 ? planMilestones(plan, total, orderDate, dispatch) : [],
        advance_received: advance ?? (q("#sale-advance").value.trim() || 0), // unreadable text: the server says so
      });
      closeSheet();
      const target = `#/customers/${r.customer_id}`;
      if (location.hash === target) window.dispatchEvent(new HashChangeEvent("hashchange")); // redraw the page
      else location.hash = target;
      toast("Sale saved");
    } catch (err) {
      if (stillOpen()) showError(err.message);
    } finally {
      save.disabled = false;
    }
  });

  // Customers for the search list, then any prefill (e.g. a bill scanned elsewhere).
  api("/api/book").then((book) => {
    customers = [...book.customers].sort((a, b) => a.name.localeCompare(b.name));
    if (!stillOpen()) return;
    if (Object.keys(prefill).length) fill(prefill);
    if (document.activeElement === custInput && !chosen) drawList();
  }).catch((e) => { if (stillOpen()) showError(e.message); });
  preview();
}
