const stateEl = document.querySelector("#market-state");
const pillEl = document.querySelector(".market-pill");
const countEl = document.querySelector("#universe-count");
const scanStateEl = document.querySelector("#scan-state");
const scanMessageEl = document.querySelector("#scan-message");
const clockEl = document.querySelector("#clock");

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
  } catch (error) {
    stateEl.textContent = "API offline";
    scanMessageEl.textContent = error.message;
  }
}

updateClock();
setInterval(updateClock, 1000);
loadDashboard();
