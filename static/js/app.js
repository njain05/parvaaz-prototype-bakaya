// Router: #/today (default), #/customers, #/customers/<id>, #/ask.
// Each screen module renders into a fresh element, so a slow fetch for a screen
// the owner already left writes into a detached node instead of the page.

import { $ } from "./lib.js";
import * as today from "./today.js";
import * as customers from "./customers.js";
import * as customer from "./customer.js";
import * as ask from "./ask.js";
import { openAddSale } from "./add-sale.js";

// Which tab a customer page belongs to: the list the owner came from.
let lastList = "today";

function route() {
  const hash = location.hash || "#/today";
  const m = hash.match(/^#\/customers\/(\d+)$/);
  if (m) return { tab: lastList, render: (el) => customer.render(el, Number(m[1])) };
  if (hash === "#/customers") return { tab: "customers", render: customers.render };
  if (hash === "#/ask") return { tab: "ask", render: ask.render };
  if (hash !== "#/today") history.replaceState(null, "", "#/today");
  return { tab: "today", render: today.render };
}

function show() {
  const { tab, render } = route();
  if (tab === "today" || tab === "customers") lastList = tab;
  document.querySelectorAll("[data-tab]").forEach((a) => {
    if (a.dataset.tab === tab) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  const view = $("#view");
  const el = document.createElement("div");
  view.replaceChildren(el);
  render(el);
}

window.addEventListener("hashchange", () => { show(); window.scrollTo(0, 0); });
document.querySelectorAll("[data-add-sale]").forEach((b) => b.addEventListener("click", () => openAddSale()));
show();
