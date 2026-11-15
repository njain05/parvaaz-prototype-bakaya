// Ask: questions about customers and payments, in any of the four languages.

import { $, esc, postJSON, getStatus } from "./lib.js";

const SUGGESTED = ["Who owes the most?", "Is hafte kitna paisa aana hai?", "Who promised to pay?"];

export function render(el) {
  el.innerHTML = `
    <div class="page-head">
      <h1 class="page-title">Ask</h1>
      <p class="soft">Ask about your customers and payments in your own words. English, Hindi, Hinglish or Punjabi.</p>
    </div>
    <div class="ask-suggest">${SUGGESTED.map((q) => `<button class="btn" type="button">${esc(q)}</button>`).join("")}</div>
    <ol class="chat" id="chat" aria-live="polite"></ol>
    <form class="ask-form" id="ask-form">
      <label for="ask-input" class="visually-hidden">Your question</label>
      <input id="ask-input" class="input" type="text" placeholder="e.g. Sharma ka kitna baaki hai?" autocomplete="off">
      <button class="btn btn-primary" type="submit">Ask</button>
    </form>
    <p class="ask-status" id="ask-status"></p>`;

  const input = $("#ask-input", el);
  el.querySelectorAll(".ask-suggest .btn").forEach((b) => b.addEventListener("click", () => ask(el, b.textContent)));
  $("#ask-form", el).addEventListener("submit", (e) => { e.preventDefault(); ask(el, input.value); });

  getStatus().then((s) => {
    $("#ask-status", el).textContent = s.ai_enabled
      ? "AI is on"
      : "AI is off: answers use simple rules. Add an API key to turn it on.";
  }).catch(() => {});
}

async function ask(el, question) {
  question = question.trim();
  if (!question) return;
  const input = $("#ask-input", el);
  input.value = "";
  const item = document.createElement("li");
  item.innerHTML = `<p class="chat-q">${esc(question)}</p><p class="chat-a soft">Thinking…</p>`;
  $("#chat", el).appendChild(item);
  const answer = item.querySelector(".chat-a");
  try {
    const r = await postJSON("/api/ai/ask", { question });
    answer.classList.remove("soft");
    answer.innerHTML = esc(r.answer) + (r.note ? `<span class="chat-note">${esc(r.note)}</span>` : "");
  } catch (e) {
    answer.className = "chat-a error";
    answer.textContent = e.message;
  }
  input.scrollIntoView({ block: "nearest" });
}
