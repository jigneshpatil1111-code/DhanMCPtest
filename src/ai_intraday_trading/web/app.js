const stateEl = document.querySelector("#market-state");
const pillEl = document.querySelector(".market-pill");
const countEl = document.querySelector("#universe-count");
const scanStateEl = document.querySelector("#scan-state");
const scanMessageEl = document.querySelector("#scan-message");
const clockEl = document.querySelector("#clock");
const emptyStateEl = document.querySelector("#empty-state");
const signalGridEl = document.querySelector("#signal-grid");

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character]);
}

function renderSignals(signals) {
  emptyStateEl.hidden = signals.length > 0;
  signalGridEl.innerHTML = signals.map((signal) => `
    <article class="signal-card">
      <div class="signal-card-head"><strong>${escapeHtml(signal.symbol)}</strong><span>${escapeHtml(signal.strategy_name.replaceAll("_", " "))}</span></div>
      <dl>
        <div><dt>Entry</dt><dd>${Number(signal.entry_price).toFixed(2)}</dd></div>
        <div><dt>Stop</dt><dd>${Number(signal.stop_loss).toFixed(2)}</dd></div>
        <div><dt>Target</dt><dd>${Number(signal.target_price).toFixed(2)}</dd></div>
        <div><dt>Qty</dt><dd>${escapeHtml(signal.quantity)}</dd></div>
      </dl>
      <time>${new Date(signal.created_at).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" })}</time>
    </article>
  `).join("");
}

function updateClock() {
  clockEl.textContent = new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date()) + " IST";
}

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard");
    if (!response.ok) throw new Error("Dashboard API unavailable");
    const data = await response.json();
    const marketOpen = data.system.market_state === "open";
    stateEl.textContent = marketOpen ? "Market open" : "Market closed";
    pillEl.classList.toggle("open", marketOpen);
    countEl.textContent = data.universe.count;
    scanStateEl.textContent = data.scan.state === "ready_for_live_data" ? "READY" : "WAIT";
    scanMessageEl.textContent = data.scan.message;
    renderSignals(data.scan.candidates);
  } catch (error) {
    stateEl.textContent = "API offline";
    scanMessageEl.textContent = error.message;
  }
}

updateClock();
setInterval(updateClock, 1000);
loadDashboard();
setInterval(loadDashboard, 15000);
