// Send reminder sheet. Stub until T07 builds it.

import { openSheet } from "./lib.js";

export function openReminder(customerId, orderId, { onSent } = {}) {
  openSheet(`
    <div class="sheet-body">
      <div class="sheet-grip" aria-hidden="true"></div>
      <div class="sheet-head">
        <h2 class="sheet-title" id="sheet-title">Send reminder</h2>
        <button class="btn btn-link sheet-close" type="button" data-close>Close</button>
      </div>
      <p class="coming-soon">Coming soon: draft a reminder and send it on WhatsApp.</p>
    </div>`);
}
