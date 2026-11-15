// Shared helpers for every screen. Plain ES module, no build step.

export const $ = (sel, el = document) => el.querySelector(sel);

// ---------- data ----------
export async function api(path, opts = {}) {
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `Something went wrong (${r.status}). Please try again.`);
  return data;
}
export const postJSON = (path, body) =>
  api(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
export const del = (path) => api(path, { method: "DELETE" });

let statusPromise = null;
// /api/status, fetched once: {ai_enabled, business_name}
export function getStatus() {
  statusPromise ??= api("/api/status").catch((e) => { statusPromise = null; throw e; });
  return statusPromise;
}

export function store(key, value) {
  try {
    if (value === undefined) return localStorage.getItem(key);
    localStorage.setItem(key, value);
  } catch { return null; }
}

// ---------- words and numbers ----------
export const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const inr = (n) => "₹" + Math.round(n).toLocaleString("en-IN");
export function lakh(n) {
  if (Math.abs(n) < 100000) return inr(n);
  return "₹" + (n / 100000).toFixed(2).replace(/\.?0+$/, "") + " lakh";
}

const pad = (n) => String(n).padStart(2, "0");
const toISO = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// "15 Nov", or "15 Nov 2025" when the year isn't this year (or withYear is set).
export function fmtDate(iso, withYear = false) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[m - 1]}` + (withYear || y !== new Date().getFullYear() ? ` ${y}` : "");
}
export function addDays(iso, n) {
  const d = new Date(iso + "T00:00:00");
  d.setDate(d.getDate() + n);
  return toISO(d);
}
export const daysBetween = (a, b) => Math.round((Date.parse(b) - Date.parse(a)) / 86400000);

export function whatsappUrl(phone, text) {
  let digits = String(phone || "").replace(/\D/g, "");
  if (digits.length === 10) digits = "91" + digits;
  if (digits.length !== 12) digits = ""; // no valid number: WhatsApp lets you pick the contact
  return `https://wa.me/${digits}?text=${encodeURIComponent(text)}`;
}

// ---------- toast ----------
let toastTimer;
// toast("Reminder sent", {action: {label: "Undo", onClick}})
export function toast(text, { action } = {}) {
  const el = $("#toast"), btn = $("#toast-action");
  $("#toast-text").textContent = text;
  btn.hidden = !action;
  btn.onclick = null;
  if (action) {
    btn.textContent = action.label;
    btn.onclick = () => { el.hidden = true; clearTimeout(toastTimer); action.onClick(); };
  }
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, action ? 6000 : 3000);
}

// ---------- sheet ----------
// A bottom sheet on phones, a centred panel on desktop (see .sheet in style.css).
// The html usually starts with <div class="sheet-body">. Any [data-close] button closes it;
// so do Escape (native <dialog>) and a tap on the backdrop.
const sheet = () => $("#sheet");
export function openSheet(html) {
  const el = sheet();
  el.innerHTML = html;
  if (!el.open) el.showModal();
  return el;
}
export function closeSheet() {
  const el = sheet();
  if (el.open) el.close();
}
document.addEventListener("click", (e) => {
  const el = sheet();
  if (!el?.open) return;
  if (e.target === el || e.target.closest("#sheet [data-close]")) closeSheet();
});
