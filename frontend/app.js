const API = "";

const categorySelect = document.getElementById("category");
const resumeFilesInput = document.getElementById("resumeFiles");
const dropzone = document.getElementById("dropzone");
const dropzoneFiles = document.getElementById("dropzoneFiles");
const analyzeBtn = document.getElementById("analyzeBtn");
const uploadStatus = document.getElementById("uploadStatus");
const candidateList = document.getElementById("candidateList");
const reportBtn = document.getElementById("reportBtn");
const statsBar = document.getElementById("statsBar");
const controlsBar = document.getElementById("controlsBar");
const searchInput = document.getElementById("searchInput");
const filterSelect = document.getElementById("filterSelect");
const sortSelect = document.getElementById("sortSelect");
const toastContainer = document.getElementById("toastContainer");

let allCandidates = [];

function showToast(kind, message) {
  const toast = document.createElement("div");
  toast.className = `toast ${kind}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("visible"));
  setTimeout(() => {
    toast.classList.remove("visible");
    setTimeout(() => toast.remove(), 250);
  }, 3200);
}

async function loadCategories() {
  try {
    const res = await fetch(`${API}/api/categories`);
    if (!res.ok) throw new Error("bad response");
    const data = await res.json();
    categorySelect.innerHTML = data.categories
      .map((c) => `<option value="${c}">${c.replaceAll("-", " ")}</option>`)
      .join("");
  } catch (e) {
    showToast("error", "Couldn't load job categories. Refresh the page.");
  }
}

function fitClass(fitCategory) {
  if (fitCategory === "Strong Fit") return "strong";
  if (fitCategory === "Moderate Fit") return "moderate";
  return "weak";
}

function setStatus(kind, html) {
  uploadStatus.className = `status-banner ${kind}`;
  uploadStatus.innerHTML = html;
}

function updateDropzoneFiles() {
  const files = resumeFilesInput.files;
  dropzoneFiles.textContent = files.length
    ? `${files.length} file${files.length > 1 ? "s" : ""} selected: ${Array.from(files).map((f) => f.name).join(", ")}`
    : "";
}

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("drag-active");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-active"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag-active");
  const dropped = Array.from(e.dataTransfer.files).filter((f) => f.type === "application/pdf");
  if (!dropped.length) {
    setStatus("error", "Only PDF files are accepted.");
    return;
  }
  const dt = new DataTransfer();
  dropped.forEach((f) => dt.items.add(f));
  resumeFilesInput.files = dt.files;
  updateDropzoneFiles();
});
resumeFilesInput.addEventListener("change", updateDropzoneFiles);

function scoreGauge(score, fitCategory) {
  const r = 22;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - Math.max(0, Math.min(100, score)) / 100);
  return `
    <div class="score-gauge">
      <svg viewBox="0 0 54 54">
        <circle class="track" cx="27" cy="27" r="${r}"></circle>
        <circle class="fill ${fitClass(fitCategory)}" cx="27" cy="27" r="${r}"
          stroke-dasharray="${c}" stroke-dashoffset="${offset}"></circle>
      </svg>
      <div class="score-gauge-label">${Math.round(score)}</div>
    </div>
  `;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function renderCandidate(c) {
  const pred = c.prediction;
  const score = c.modified_score ?? pred.fit_score;
  const shapItems = pred.top_features
    .map((f) => {
      const cls = f.impact >= 0 ? "positive" : "negative";
      const sign = f.impact >= 0 ? "+" : "";
      return `<li class="${cls}">${escapeHtml(f.feature)}: ${sign}${f.impact} impact</li>`;
    })
    .join("");

  const decisionArea = c.decision
    ? `
      <div class="stamp-row">
        <span class="stamp ${c.decision}">${c.decision}</span>
        ${c.decision_reason ? `<span class="stamp-reason">"${escapeHtml(c.decision_reason)}"</span>` : ""}
      </div>
    `
    : `
      <div class="decision-row" data-mode="default">
        <input type="text" placeholder="Reason (required)" class="reason-input" />
        <button class="small approve" data-action="approve">Approve</button>
        <button class="small reject" data-action="reject">Reject</button>
        <button class="small modify" data-action="modify">Modify Score</button>
      </div>
      <div class="decision-row modify-form" data-mode="modify" hidden>
        <input type="text" placeholder="Reason (required)" class="reason-input" />
        <input type="number" min="0" max="100" step="0.1" placeholder="0-100" class="score-input" />
        <button class="small modify" data-action="modify-confirm">Save score</button>
        <button class="small ghost" data-action="modify-cancel">Cancel</button>
      </div>
    `;

  return `
    <div class="candidate-card" data-id="${c.id}">
      <div class="candidate-top">
        <div>
          <div class="candidate-name">${escapeHtml(c.filename)}</div>
          <div class="candidate-meta">${escapeHtml(c.category.replaceAll("-", " "))}</div>
        </div>
        <span class="badge ${fitClass(pred.fit_category)}">${pred.fit_category}</span>
      </div>

      <div class="score-row">
        ${scoreGauge(score, pred.fit_category)}
        <div class="score-meta">
          <span><strong>${score}</strong> / 100 fit score</span>
          <span>${pred.confidence}% confidence · ${pred.raw_features.years_experience} yrs experience</span>
        </div>
      </div>

      ${pred.narration ? `<p class="narration">${escapeHtml(pred.narration)}</p>` : ""}
      <ul class="shap-list">${shapItems}</ul>

      ${decisionArea}
    </div>
  `;
}

const emptyStateHtml = `
  <div class="empty-state">
    <svg viewBox="0 0 24 24" width="30" height="30" aria-hidden="true">
      <path d="M4 5a2 2 0 012-2h8l6 6v10a2 2 0 01-2 2H6a2 2 0 01-2-2V5z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
      <path d="M14 3v6h6" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/>
    </svg>
    <p>No candidates yet — analyze some resumes above to start reviewing.</p>
  </div>
`;

const noMatchesHtml = `
  <div class="empty-state">
    <p>No candidates match the current search/filter.</p>
  </div>
`;

function updateStats(candidates) {
  const total = candidates.length;
  const approved = candidates.filter((c) => c.decision === "approve").length;
  const rejected = candidates.filter((c) => c.decision === "reject").length;
  const pending = candidates.filter((c) => !c.decision).length;
  const avg = total
    ? (candidates.reduce((sum, c) => sum + (c.modified_score ?? c.prediction.fit_score), 0) / total).toFixed(1)
    : "–";

  document.getElementById("statTotal").textContent = total;
  document.getElementById("statApproved").textContent = approved;
  document.getElementById("statRejected").textContent = rejected;
  document.getElementById("statPending").textContent = pending;
  document.getElementById("statAvg").textContent = avg;

  statsBar.hidden = total === 0;
  controlsBar.hidden = total === 0;
}

function applyFiltersAndSort() {
  const query = searchInput.value.trim().toLowerCase();
  const filter = filterSelect.value;
  const sort = sortSelect.value;

  let visible = allCandidates.filter((c) => {
    if (query && !c.filename.toLowerCase().includes(query)) return false;
    if (filter === "pending") return !c.decision;
    if (filter === "all") return true;
    return c.decision === filter;
  });

  visible.sort((a, b) => {
    const scoreA = a.modified_score ?? a.prediction.fit_score;
    const scoreB = b.modified_score ?? b.prediction.fit_score;
    switch (sort) {
      case "score-asc":
        return scoreA - scoreB;
      case "name-asc":
        return a.filename.localeCompare(b.filename);
      case "confidence-desc":
        return b.prediction.confidence - a.prediction.confidence;
      case "score-desc":
      default:
        return scoreB - scoreA;
    }
  });

  if (!allCandidates.length) {
    candidateList.innerHTML = emptyStateHtml;
  } else if (!visible.length) {
    candidateList.innerHTML = noMatchesHtml;
  } else {
    candidateList.innerHTML = visible.map(renderCandidate).join("");
  }
}

async function refreshCandidates() {
  try {
    const res = await fetch(`${API}/api/candidates`);
    if (!res.ok) throw new Error("bad response");
    const data = await res.json();
    allCandidates = data.candidates;
    updateStats(allCandidates);
    applyFiltersAndSort();
  } catch (e) {
    showToast("error", "Couldn't load candidates. Check your connection and retry.");
  }
}

searchInput.addEventListener("input", applyFiltersAndSort);
filterSelect.addEventListener("change", applyFiltersAndSort);
sortSelect.addEventListener("change", applyFiltersAndSort);

analyzeBtn.addEventListener("click", async () => {
  const files = resumeFilesInput.files;
  if (!files.length) {
    setStatus("error", "Choose at least one resume PDF first.");
    return;
  }
  const category = categorySelect.value;
  analyzeBtn.disabled = true;
  analyzeBtn.classList.add("busy");

  const errors = [];
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    setStatus("info", `Analyzing ${i + 1} of ${files.length}: ${file.name}…`);
    const formData = new FormData();
    formData.append("category", category);
    formData.append("file", file);
    try {
      const res = await fetch(`${API}/api/analyze-resume`, { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json();
        errors.push(`${file.name}: ${err.detail}`);
      }
    } catch (e) {
      errors.push(`${file.name}: network error`);
    }
  }

  analyzeBtn.disabled = false;
  analyzeBtn.classList.remove("busy");
  resumeFilesInput.value = "";
  updateDropzoneFiles();
  await refreshCandidates();

  if (errors.length) {
    setStatus("error", `${files.length - errors.length} of ${files.length} analyzed. Failures:<ul>${errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("")}</ul>`);
  } else {
    setStatus("success", `Analyzed ${files.length} resume${files.length > 1 ? "s" : ""}.`);
    showToast("success", `Analyzed ${files.length} resume${files.length > 1 ? "s" : ""}.`);
  }
});

candidateList.addEventListener("click", async (e) => {
  const action = e.target.dataset.action;
  if (!action) return;

  const card = e.target.closest(".candidate-card");
  const candidateId = card.dataset.id;

  if (action === "modify") {
    card.querySelector('.decision-row[data-mode="default"]').hidden = true;
    card.querySelector('.decision-row[data-mode="modify"]').hidden = false;
    return;
  }
  if (action === "modify-cancel") {
    card.querySelector('.decision-row[data-mode="modify"]').hidden = true;
    card.querySelector('.decision-row[data-mode="default"]').hidden = false;
    return;
  }

  const activeRow = action === "modify-confirm"
    ? card.querySelector('.decision-row[data-mode="modify"]')
    : card.querySelector('.decision-row[data-mode="default"]');
  const reasonInput = activeRow.querySelector(".reason-input");
  const reason = reasonInput.value.trim();

  if (!reason) {
    reasonInput.placeholder = "Reason is required!";
    reasonInput.classList.add("invalid");
    return;
  }

  let modifiedScore = null;
  let decision = action;
  if (action === "modify-confirm") {
    decision = "modify";
    const scoreInput = activeRow.querySelector(".score-input");
    modifiedScore = parseFloat(scoreInput.value);
    if (isNaN(modifiedScore) || modifiedScore < 0 || modifiedScore > 100) {
      scoreInput.classList.add("invalid");
      scoreInput.placeholder = "0-100 required";
      return;
    }
  }

  try {
    const res = await fetch(`${API}/api/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_id: candidateId,
        decision,
        reason,
        modified_score: modifiedScore,
      }),
    });
    if (!res.ok) throw new Error("bad response");
    showToast("success", `Marked as ${decision}.`);
  } catch (err) {
    showToast("error", "Couldn't save the decision. Try again.");
  }

  await refreshCandidates();
});

reportBtn.addEventListener("click", () => {
  window.open(`${API}/api/report`, "_blank");
});

loadCategories();
refreshCandidates();
