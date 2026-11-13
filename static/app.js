// Bakaya front end: plain JavaScript, no build step.

const $ = (sel, el = document) => el.querySelector(sel);
let BOOK = null;
let STATUS = { ai_enabled: false, business_name: "" };

// ---------- helpers ----------
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
const lakh = (n) => (n >= 100000 ? "₹" + (n / 100000).toFixed(1).replace(/\.0$/, "") + " lakh" : inr(n));
const pad = (n) => String(n).padStart(2, "0");
const toISO = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const addDays = (iso, n) => { const d = new Date(iso + "T00:00:00"); d.setDate(d.getDate() + n); return toISO(d); };
const fmtDate = (iso) => new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
const daysBetween = (a, b) => Math.round((new Date(b + "T00:00:00") - new Date(a + "T00:00:00")) / 86400000);

function store(key, value) {
  try { if (value === undefined) return localStorage.getItem(key); localStorage.setItem(key, value); } catch { return null; }
}

async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `Request failed (${r.status})`);
  return data;
}
const postJSON = (path, body) => api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

function toast(text) {
  const t = $("#toast");
  t.textContent = text;
  t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.hidden = true), 2600);
}

const STATUS_BADGE = { overdue: ["red", "Overdue"], due_soon: ["amber", "Due soon"], on_track: ["blue", "On track"], paid: ["green", "Paid"] };
const HABIT_BADGE = { often_late: ["red", "Often late"], sometimes_late: ["amber", "Sometimes late"], on_time: ["green", "Pays on time"], new: ["grey", "New customer"] };
const badge = ([cls, text], title = "") => `<span class="badge ${cls}" ${title ? `title="${esc(title)}"` : ""}>${esc(text)}</span>`;

// ---------- modal ----------
function openModal(html) {
  $("#modal-body").innerHTML = `<div class="modal-content">${html}</div>`;
  const m = $("#modal");
  if (!m.open) m.showModal();
}
function closeModal() { $("#modal").close(); }

// ---------- tabs ----------
function showTab(name) {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === name));
  document.querySelectorAll("main > section").forEach((s) => (s.hidden = s.id !== `tab-${name}`));
  store("tab", name);
}
document.querySelectorAll(".tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));

// ---------- load ----------
async function load() {
  BOOK = await api("/api/book");
  renderDashboard();
  renderOrders();
}

async function init() {
  STATUS = await api("/api/status");
  const pill = $("#ai-pill");
  pill.textContent = STATUS.ai_enabled ? "AI: on" : "AI: offline demo mode";
  pill.className = "pill " + (STATUS.ai_enabled ? "on" : "off");
  pill.title = STATUS.ai_enabled ? "Reminders and answers are written by Claude" : "Add ANTHROPIC_API_KEY to .env to turn on AI. Templates and simple rules are used until then.";
  $("#biz-name").textContent = `${STATUS.business_name} · Credit & payment tracker`;
  setupAsk();
  setupScan();
  await load();
  showTab(store("tab") || "dashboard");
}

// ---------- dashboard ----------
function renderDashboard() {
  const t = BOOK.totals;
  const openOrders = BOOK.orders.filter((o) => o.balance > 0.5).length;
  $("#stats").innerHTML = `
    <div class="stat"><div class="label">Total outstanding</div><div class="value">${lakh(t.outstanding)}</div><div class="sub">across ${openOrders} open orders</div></div>
    <div class="stat red"><div class="label">Overdue</div><div class="value">${lakh(t.overdue)}</div><div class="sub">${t.customers_overdue} customers are late</div></div>
    <div class="stat amber"><div class="label">Due in next 7 days</div><div class="value">${lakh(t.due_this_week)}</div><div class="sub">follow up before it's late</div></div>
    <div class="stat"><div class="label">Overdue for 60+ days</div><div class="value">${lakh(BOOK.ageing["61-90"] + BOOK.ageing["90+"])}</div><div class="sub">highest risk of never coming</div></div>`;

  const buckets = [["1-30", "1–30 days", "var(--amber)"], ["31-60", "31–60 days", "#d9822b"], ["61-90", "61–90 days", "var(--red)"], ["90+", "90+ days", "#8f1f1f"]];
  const max = Math.max(1, ...Object.values(BOOK.ageing));
  $("#ageing").innerHTML = buckets.map(([k, label, color]) => `
    <div class="bucket">
      <div class="amt">${inr(BOOK.ageing[k])}</div>
      <div class="bar-track"><div class="bar" style="width:${(BOOK.ageing[k] / max) * 100}%;background:${color}"></div></div>
      <div class="lbl">${label} late</div>
    </div>`).join("");

  $("#today").textContent = `As of ${fmtDate(BOOK.today)}`;
  const rows = BOOK.customers.filter((c) => c.outstanding > 0.5);
  $("#cust-table").innerHTML = `
    <thead><tr><th>Customer</th><th class="num">Outstanding</th><th class="num">Overdue</th><th class="num hide-sm">Late by</th><th>Payment habit</th><th></th></tr></thead>
    <tbody>${rows.map((c) => `
      <tr class="clickable" data-order="${c.remind_order_id ?? ""}">
        <td><strong>${esc(c.name)}</strong><span class="sub">${esc(c.city)} · ${c.orders} order${c.orders > 1 ? "s" : ""}</span></td>
        <td class="num">${inr(c.outstanding)}</td>
        <td class="num" style="${c.overdue > 0.5 ? "color:var(--red);font-weight:700" : ""}">${c.overdue > 0.5 ? inr(c.overdue) : "—"}</td>
        <td class="num hide-sm">${c.days_overdue ? `${c.days_overdue} days` : "—"}</td>
        <td>${badge(HABIT_BADGE[c.habit], c.avg_days_late != null ? `Pays ${c.avg_days_late} days late on average` : "")}</td>
        <td class="num">${c.remind_order_id ? `<button class="btn small" data-remind="${c.remind_order_id}">Remind</button>` : ""}</td>
      </tr>`).join("")}</tbody>`;

  $("#cust-table").querySelectorAll("tr[data-order]").forEach((tr) => tr.addEventListener("click", (e) => {
    const remind = e.target.closest("[data-remind]");
    if (remind) return openReminder(Number(remind.dataset.remind));
    if (tr.dataset.order) openOrder(Number(tr.dataset.order));
  }));
}

// ---------- orders ----------
function nextLine(o) {
  if (o.status === "paid") return `<span class="muted">Fully paid</span>`;
  if (o.overdue > 0.5) return `<span style="color:var(--red);font-weight:600">${inr(o.overdue)} overdue</span><span class="sub">${o.days_overdue} days late</span>`;
  if (o.next_due) return `${inr(o.next_due.amount)}<span class="sub">due ${fmtDate(o.next_due.due_date)}</span>`;
  return "";
}

function renderOrders() {
  $("#orders-table").innerHTML = `
    <thead><tr><th>Order</th><th>Customer</th><th class="hide-sm">Machine</th><th class="num">Total</th><th class="num">Balance</th><th>Status</th><th class="num">Next</th></tr></thead>
    <tbody>${BOOK.orders.map((o) => `
      <tr class="clickable" data-id="${o.id}">
        <td>#${o.id}<span class="sub">${fmtDate(o.order_date)}</span></td>
        <td><strong>${esc(o.customer_name)}</strong><span class="sub">${esc(o.city)}</span></td>
        <td class="hide-sm">${esc(o.machine)}</td>
        <td class="num">${inr(o.total)}</td>
        <td class="num">${o.balance > 0.5 ? inr(o.balance) : "—"}</td>
        <td>${badge(STATUS_BADGE[o.status])}</td>
        <td class="num">${nextLine(o)}</td>
      </tr>`).join("")}</tbody>`;
  $("#orders-table").querySelectorAll("tr[data-id]").forEach((tr) => tr.addEventListener("click", () => openOrder(Number(tr.dataset.id))));
}

function milestoneStatus(m) {
  if (m.status === "paid") return badge(["green", m.paid_on ? `Paid ${fmtDate(m.paid_on)}` : "Paid"]);
  if (m.status === "overdue") {
    const late = daysBetween(m.due_date, BOOK.today);
    return badge(["red", m.partly_paid ? `${inr(m.unpaid)} left · ${late} days late` : `Overdue · ${late} days`]);
  }
  return badge(["blue", m.partly_paid ? `${inr(m.unpaid)} left` : "Upcoming"]);
}

function openOrder(id) {
  const o = BOOK.orders.find((x) => x.id === id);
  if (!o) return;
  const suggested = Math.min(o.balance, o.overdue > 0.5 ? o.overdue : o.next_due ? o.next_due.amount : o.balance);
  openModal(`
    <h3>#${o.id} · ${esc(o.machine)}</h3>
    <div class="muted">${esc(o.customer_name)}, ${esc(o.city)} · ordered ${fmtDate(o.order_date)} · ${badge(STATUS_BADGE[o.status])}</div>
    <div class="kv">
      <div><div class="k">Total</div><div class="v">${inr(o.total)}</div></div>
      <div><div class="k">Received</div><div class="v">${inr(o.paid)}</div></div>
      <div><div class="k">Balance</div><div class="v" style="${o.overdue > 0.5 ? "color:var(--red)" : ""}">${inr(o.balance)}</div></div>
    </div>
    <div class="subhead">Payment plan</div>
    <table><tbody>${o.milestones.map((m) => `
      <tr><td>${esc(m.label)}<span class="sub">due ${fmtDate(m.due_date)}</span></td><td class="num">${inr(m.amount)}</td><td class="num">${milestoneStatus(m)}</td></tr>`).join("")}
    </tbody></table>
    <div class="subhead">Payments received</div>
    ${o.payments.length ? `<table><tbody>${o.payments.map((p) => `
      <tr><td>${fmtDate(p.date)}<span class="sub">${esc([p.mode, p.note].filter(Boolean).join(" · "))}</span></td><td class="num">${inr(p.amount)}</td></tr>`).join("")}
    </tbody></table>` : `<div class="empty">No payments yet.</div>`}
    ${o.balance > 0.5 ? `
      <div class="subhead">Record a payment</div>
      <form id="pay-form" class="grid2">
        <label class="field">Amount received (₹)<input name="amount" type="number" min="1" step="1" value="${Math.round(suggested)}" required></label>
        <label class="field">Date<input name="date" type="date" value="${BOOK.today}" required></label>
        <label class="field">Mode<select name="mode"><option>NEFT</option><option>RTGS</option><option>UPI</option><option>Cheque</option><option>Cash</option></select></label>
        <label class="field">Note<input name="note" placeholder="Cheque no., UTR, etc."></label>
      </form>
      <div id="pay-error" class="error"></div>
      <div class="actions">
        <button class="btn" id="remind-btn">Send reminder</button>
        <button class="btn primary" id="pay-btn">Save payment</button>
      </div>` : ""}`);

  if (o.balance > 0.5) {
    $("#remind-btn").onclick = () => openReminder(o.id);
    $("#pay-btn").onclick = async () => {
      const f = new FormData($("#pay-form"));
      try {
        await postJSON(`/api/orders/${o.id}/payments`, Object.fromEntries(f));
        await load();
        openOrder(o.id);
        toast(`Payment of ${inr(Number(f.get("amount")))} recorded`);
      } catch (e) { $("#pay-error").textContent = e.message; }
    };
  }
}

// ---------- reminders ----------
function whatsappUrl(phone, text) {
  let digits = String(phone || "").replace(/\D/g, "");
  if (digits.length === 10) digits = "91" + digits;
  if (digits.length !== 12) digits = ""; // no valid number: WhatsApp lets you pick the contact
  return `https://wa.me/${digits}?text=${encodeURIComponent(text)}`;
}

function openReminder(orderId) {
  const o = BOOK.orders.find((x) => x.id === orderId);
  const lang = store("lang") || "hinglish";
  openModal(`
    <h3>Payment reminder</h3>
    <div class="muted">${esc(o.customer_name)} · #${o.id} ${esc(o.machine)} · ${o.overdue > 0.5 ? `<strong style="color:var(--red)">${inr(o.overdue)} overdue</strong>` : `${inr(o.next_due?.amount || o.balance)} due ${o.next_due ? fmtDate(o.next_due.due_date) : ""}`}</div>
    <label class="field">Language
      <select id="rem-lang">
        ${[["hinglish", "Hinglish"], ["hindi", "Hindi (हिंदी)"], ["punjabi", "Punjabi (ਪੰਜਾਬੀ)"], ["english", "English"]]
          .map(([v, l]) => `<option value="${v}" ${v === lang ? "selected" : ""}>${l}</option>`).join("")}
      </select>
    </label>
    <textarea id="rem-text" placeholder="Writing…"></textarea>
    <div id="rem-src" class="muted small"></div>
    <div class="actions">
      <button class="btn" id="rem-again">Rewrite</button>
      <button class="btn" id="rem-copy">Copy</button>
      <button class="btn whatsapp" id="rem-wa">Open in WhatsApp</button>
    </div>`);

  let phone = "";
  const write = async () => {
    const language = $("#rem-lang").value;
    store("lang", language);
    $("#rem-text").value = "";
    $("#rem-text").placeholder = STATUS.ai_enabled ? "AI is writing the reminder…" : "Writing…";
    $("#rem-src").textContent = "";
    try {
      const r = await postJSON("/api/ai/reminder", { order_id: orderId, language });
      phone = r.phone;
      $("#rem-text").value = r.message;
      $("#rem-src").innerHTML = (r.source === "ai" ? "✨ Written by AI. Check it, edit if needed, then send." : "Written from a template (offline mode). Edit if needed.") + (r.note ? `<div class="note">${esc(r.note)}</div>` : "");
    } catch (e) { $("#rem-src").innerHTML = `<span class="error">${esc(e.message)}</span>`; }
  };
  $("#rem-lang").onchange = write;
  $("#rem-again").onclick = write;
  $("#rem-copy").onclick = async () => {
    try { await navigator.clipboard.writeText($("#rem-text").value); toast("Copied"); } catch { $("#rem-text").select(); }
  };
  $("#rem-wa").onclick = () => window.open(whatsappUrl(phone, $("#rem-text").value), "_blank");
  write();
}

// ---------- new order ----------
function planMilestones(plan, total, orderDate, dispatchDate) {
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

function openNewOrder(prefill = {}) {
  const match = prefill.customer_name
    ? BOOK.customers.find((c) => c.name.toLowerCase() === prefill.customer_name.toLowerCase())
    : null;
  const isNew = prefill.customer_name && !match;
  const orderDate = /^\d{4}-\d{2}-\d{2}$/.test(prefill.invoice_date || "") ? prefill.invoice_date : BOOK.today;
  openModal(`
    <h3>New order</h3>
    ${prefill.customer_name ? `<div class="note">Filled in from the scanned bill. Please check every field before saving.</div>` : ""}
    <form id="order-form" class="modal-content">
      <label class="field">Customer
        <select name="customer_id" id="cust-select">
          <option value="">Choose a customer…</option>
          ${BOOK.customers.map((c) => `<option value="${c.id}" ${match && match.id === c.id ? "selected" : ""}>${esc(c.name)} (${esc(c.city)})</option>`).join("")}
          <option value="__new" ${isNew ? "selected" : ""}>+ New customer</option>
        </select>
      </label>
      <div id="new-cust" class="grid2" ${isNew ? "" : "hidden"}>
        <label class="field">Firm name<input name="nc_name" value="${esc(prefill.customer_name || "")}"></label>
        <label class="field">Contact person<input name="nc_person" value="${esc(prefill.contact_person || "")}"></label>
        <label class="field">Phone<input name="nc_phone" value="${esc(prefill.phone || "")}"></label>
        <label class="field">City<input name="nc_city" value="${esc(prefill.city || "")}"></label>
      </div>
      <label class="field">Machine or item<input name="machine" value="${esc(prefill.item || "")}" placeholder="e.g. Raising Machine, 24 roller" required></label>
      <div class="grid2">
        <label class="field">Order date<input name="order_date" type="date" value="${orderDate}" required></label>
        <label class="field">Total amount (₹)<input name="total" type="number" min="1" step="1" value="${prefill.total_amount ? Math.round(prefill.total_amount) : ""}" required></label>
        <label class="field">Payment plan
          <select name="plan">
            <option value="30-60-10">30% advance · 60% before dispatch · 10% after installation</option>
            <option value="50-50">50% advance · 50% before dispatch</option>
            <option value="100">Full payment on delivery</option>
          </select>
        </label>
        <label class="field">Expected dispatch date<input name="dispatch" type="date" value="${addDays(orderDate, 45)}" required></label>
        <label class="field">Advance received now (₹)<input name="advance" type="number" min="0" step="1" value="${prefill.amount_paid ? Math.round(prefill.amount_paid) : 0}"></label>
      </div>
      <div class="subhead">Instalments</div>
      <div id="plan-preview"></div>
      <div id="order-error" class="error"></div>
      <div class="actions"><button type="button" class="btn" onclick="closeModal()">Cancel</button><button class="btn primary">Save order</button></div>
    </form>`);

  const form = $("#order-form");
  const preview = () => {
    const f = new FormData(form);
    const total = Number(f.get("total")) || 0;
    if (!total) { $("#plan-preview").innerHTML = `<div class="empty">Enter the total to see the instalments.</div>`; return; }
    const ms = planMilestones(f.get("plan"), total, f.get("order_date"), f.get("dispatch"));
    $("#plan-preview").innerHTML = `<table><tbody>${ms.map((m) => `<tr><td>${m.label}</td><td>${fmtDate(m.due_date)}</td><td class="num">${inr(m.amount)}</td></tr>`).join("")}</tbody></table>`;
  };
  form.addEventListener("input", preview);
  $("#cust-select").onchange = (e) => ($("#new-cust").hidden = e.target.value !== "__new");
  preview();

  form.onsubmit = async (e) => {
    e.preventDefault();
    const f = new FormData(form);
    const total = Number(f.get("total"));
    const cid = f.get("customer_id");
    const body = {
      machine: f.get("machine"),
      order_date: f.get("order_date"),
      total,
      milestones: planMilestones(f.get("plan"), total, f.get("order_date"), f.get("dispatch")),
      advance_received: Number(f.get("advance")) || 0,
    };
    if (cid === "__new") body.new_customer = { name: f.get("nc_name"), contact_person: f.get("nc_person"), phone: f.get("nc_phone"), city: f.get("nc_city") };
    else body.customer_id = cid ? Number(cid) : null;
    try {
      const r = await postJSON("/api/orders", body);
      await load();
      showTab("orders");
      openOrder(r.id);
      toast("Order saved");
    } catch (err) { $("#order-error").textContent = err.message; }
  };
}

$("#new-order-btn").onclick = () => openNewOrder();

// ---------- ask AI ----------
const EXAMPLES = ["Who owes the most?", "Is hafte kitna paisa aana hai?", "What is overdue?", "Sharma ka kitna baaki hai?", "Total outstanding kitna hai?"];

function setupAsk() {
  $("#ask-chips").innerHTML = EXAMPLES.map((q) => `<button class="chip" type="button">${esc(q)}</button>`).join("");
  $("#ask-chips").querySelectorAll(".chip").forEach((c) => (c.onclick = () => ask(c.textContent)));
  $("#ask-form").onsubmit = (e) => { e.preventDefault(); ask($("#ask-input").value); };
}

async function ask(question) {
  question = question.trim();
  if (!question) return;
  $("#ask-input").value = "";
  const chat = $("#chat");
  chat.insertAdjacentHTML("beforeend", `<div class="msg user">${esc(question)}</div>`);
  const bot = document.createElement("div");
  bot.className = "msg bot";
  bot.textContent = STATUS.ai_enabled ? "Thinking…" : "…";
  chat.appendChild(bot);
  try {
    const r = await postJSON("/api/ai/ask", { question });
    bot.innerHTML = esc(r.answer) + `<span class="src">${r.source === "ai" ? "✨ Answered by AI from your data" : "Offline answer (basic rules)"}${r.note ? " · " + esc(r.note) : ""}</span>`;
  } catch (e) { bot.innerHTML = `<span class="error">${esc(e.message)}</span>`; }
}

// ---------- scan bill ----------
function setupScan() {
  const file = $("#scan-file"), btn = $("#scan-btn");
  if (!STATUS.ai_enabled) {
    $("#scan-result").innerHTML = `<div class="note">Reading bills needs the AI. Add ANTHROPIC_API_KEY to the .env file and restart the app. You can still add orders by hand on the Orders tab.</div>`;
  }
  file.onchange = () => {
    const f = file.files[0];
    if (!f) return;
    const img = $("#scan-preview");
    img.src = URL.createObjectURL(f);
    img.hidden = false;
    btn.disabled = !STATUS.ai_enabled;
  };
  btn.onclick = async () => {
    const fd = new FormData();
    fd.append("image", file.files[0]);
    btn.disabled = true;
    btn.textContent = "Reading bill…";
    $("#scan-result").innerHTML = "";
    try {
      const r = await api("/api/ai/scan", { method: "POST", body: fd });
      const rows = [["Customer", r.customer_name], ["Contact", r.contact_person], ["Phone", r.phone], ["City", r.city],
        ["Invoice no.", r.invoice_number], ["Date", r.invoice_date ? fmtDate(r.invoice_date) : ""], ["Item", r.item],
        ["Total", r.total_amount ? inr(r.total_amount) : ""], ["Already paid", r.amount_paid ? inr(r.amount_paid) : ""]];
      $("#scan-result").innerHTML = `
        <div class="subhead">✨ AI read this from the bill</div>
        <table><tbody>${rows.map(([k, v]) => `<tr><td class="muted">${k}</td><td>${v ? esc(v) : `<span class="muted">not found</span>`}</td></tr>`).join("")}</tbody></table>
        <div class="actions"><button class="btn primary" id="scan-create">Create order from this bill</button></div>`;
      $("#scan-create").onclick = () => openNewOrder(r);
    } catch (e) {
      $("#scan-result").innerHTML = `<div class="error">${esc(e.message)}</div>`;
    } finally {
      btn.disabled = false;
      btn.textContent = "Read bill";
    }
  };
}

init().catch((e) => {
  document.querySelector("main").innerHTML = `<div class="card"><div class="error">Couldn't load the app: ${esc(e.message)}</div></div>`;
});
