const endpoint = document.body.dataset.endpoint;
const refreshButton = document.getElementById("refresh-btn");
const updatedLabel = document.getElementById("last-updated");

function statusClass(status) {
  return `status-chip status-${status || "unknown"}`;
}

function renderOverview(payload) {
  const container = document.getElementById("overview-badges");
  if (!container) return;

  const cards = payload.items
    .map(
      (item) => `
      <article class="card">
        <h3>${item.name}</h3>
        <span class="${statusClass(item.status)}">${item.status}</span>
        <p>${item.detail}</p>
        ${item.hint ? `<p><strong>Hint:</strong> ${item.hint}</p>` : ""}
      </article>
    `
    )
    .join("");

  container.innerHTML = cards;
}

function renderPipeline(payload) {
  const rows = document.getElementById("pipeline-rows");
  if (!rows) return;

  rows.innerHTML = payload.stages
    .map(
      (stage) => `
      <tr>
        <td>${stage.layer}</td>
        <td><span class="${statusClass(stage.status)}">${stage.status}</span></td>
        <td>${stage.row_count ?? "-"}</td>
        <td>${stage.last_updated ?? "-"}</td>
        <td>${stage.detail}</td>
      </tr>
    `
    )
    .join("");
}

function renderQuality(payload) {
  const rows = document.getElementById("quality-rows");
  if (!rows) return;

  rows.innerHTML = payload.checks
    .map(
      (check) => `
      <tr>
        <td>${check.name}</td>
        <td><span class="${statusClass(check.status)}">${check.status}</span></td>
        <td>${check.value}</td>
        <td>${check.detail}</td>
      </tr>
    `
    )
    .join("");
}

function renderSecurity(payload) {
  const container = document.getElementById("security-cards");
  if (!container) return;

  container.innerHTML = `
    <article class="card">
      <h3>Security Status</h3>
      <span class="${statusClass(payload.status)}">${payload.status}</span>
      <p>${payload.detail}</p>
      <p>Report: ${payload.report_path ?? "-"}</p>
      <p>High: ${payload.high_count ?? "-"}</p>
      <p>Critical: ${payload.critical_count ?? "-"}</p>
    </article>
  `;
}

function renderConfig(payload) {
  const container = document.getElementById("config-fields");
  if (!container || !payload.env_vars) return;

  container.innerHTML = Object.entries(payload.env_vars).map(([key, val]) => `
    <div class="form-group">
      <label for="env-${key}">${key}</label>
      <input type="text" id="env-${key}" name="${key}" value="${val}" class="form-control" />
    </div>
  `).join("");
}

function renderPage(payload) {
  renderOverview(payload);
  renderPipeline(payload);
  renderQuality(payload);
  renderSecurity(payload);
  renderConfig(payload);
}

async function refresh() {
  if (!endpoint) return;

  try {
    const response = await fetch(endpoint, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    renderPage(payload);
    const timestamp = payload.generated_at || new Date().toISOString();
    updatedLabel.textContent = `Last updated: ${timestamp}`;
  } catch (error) {
    updatedLabel.textContent = `Last updated: failed (${error})`;
  }
}

refreshButton?.addEventListener("click", refresh);
refresh();
if (!window.location.pathname.startsWith('/config')) {
  setInterval(refresh, 15000);
}

const configForm = document.getElementById("config-form");
if (configForm) {
  configForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const alertBox = document.getElementById("config-alert");
    const formData = new FormData(configForm);
    const env_vars = Object.fromEntries(formData.entries());

    try {
      const response = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ env_vars })
      });
      const result = await response.json();
      
      alertBox.textContent = result.message || "Saved successfully";
      alertBox.className = "alert alert-success";
      alertBox.classList.remove("hidden");
      setTimeout(() => alertBox.classList.add("hidden"), 3000);
    } catch (error) {
      alertBox.textContent = `Error: ${error.message}`;
      alertBox.className = "alert alert-danger";
      alertBox.classList.remove("hidden");
    }
  });
}

document.querySelectorAll(".action-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    const scriptName = btn.dataset.script;
    const outputBox = document.getElementById("action-output");
    
    btn.disabled = true;
    btn.textContent = `Running...`;
    outputBox.textContent = `Executing ${scriptName}...\n`;
    
    try {
      const response = await fetch(`/api/action/${scriptName}`, { method: "POST" });
      const result = await response.json();
      outputBox.textContent += result.output || result.message;
      if (result.status === 'error') {
         outputBox.textContent += `\n\nFailed to execute.`;
      }
    } catch (error) {
      outputBox.textContent += `\nError: ${error.message}`;
    } finally {
      btn.disabled = false;
      btn.textContent = `▶ Run ${scriptName.replace(/_/g, ' ')}`;
    }
  });
});
