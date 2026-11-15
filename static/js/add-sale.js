// Add sale sheet. Stub until T11 builds it (typed in, or scanned from a bill).

import { openSheet } from "./lib.js";

export function openAddSale(prefill = {}) {
  openSheet(`
    <div class="sheet-body">
      <div class="sheet-grip" aria-hidden="true"></div>
      <div class="sheet-head">
        <h2 class="sheet-title" id="sheet-title">Add sale</h2>
        <button class="btn btn-link sheet-close" type="button" data-close>Close</button>
      </div>
      <p class="coming-soon">Coming soon: add a sale by typing it in or scanning a bill.</p>
    </div>`);
}
