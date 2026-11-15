// Customer page. Stub until T09 builds it on GET /api/customers/<id>.

export function render(el, id) {
  el.innerHTML = `
    <a class="back" href="#/customers">‹ Customers</a>
    <div class="page-head"><h1 class="page-title">Customer</h1></div>
    <p class="coming-soon">Coming soon: sales, instalments and history for customer ${Number(id)}.</p>`;
}
