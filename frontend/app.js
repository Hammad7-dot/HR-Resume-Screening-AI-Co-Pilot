const API = "";

const categorySelect = document.getElementById("category");
const resumeFilesInput = document.getElementById("resumeFiles");
const analyzeBtn = document.getElementById("analyzeBtn");
const uploadStatus = document.getElementById("uploadStatus");
const candidateList = document.getElementById("candidateList");
const reportBtn = document.getElementById("reportBtn");

async function loadCategories() {
  const res = await fetch(`${API}/api/categories`);
  const data = await res.json();
  categorySelect.innerHTML = data.categories
    .map((c) => `<option value="${c}">${c.replaceAll("-", " ")}</option>`)
    .join("");
}

function fitClass(fitCategory) {
  if (fitCategory === "Strong Fit") return "strong";
  if (fitCategory === "Moderate Fit") return "moderate";
  return "weak";
}

function renderCandidate(c) {
  const pred = c.prediction;
  const shapItems = pred.top_features
    .map((f) => {
      const cls = f.impact >= 0 ? "positive" : "negative";
      const sign = f.impact >= 0 ? "+" : "";
      return `<li class="${cls}">${f.feature}: ${sign}${f.impact} impact</li>`;
    })
    .join("");

  const decisionTag = c.decision
    ? `<span class="decision-tag ${c.decision}">${c.decision.toUpperCase()}${
        c.decision_reason ? " — " + c.decision_reason : ""
      }</span>`
    : "";

  return `
    <div class="candidate-card" data-id="${c.id}">
      <div class="candidate-top">
        <div>
          <div class="candidate-name">${c.filename}</div>
          <div class="candidate-meta">${c.category.replaceAll("-", " ")}</div>
        </div>
        <span class="badge ${fitClass(pred.fit_category)}">${pred.fit_category}</span>
      </div>

      <div class="score-row">
        <span><strong>Fit Score:</strong> ${c.modified_score ?? pred.fit_score} / 100</span>
        <span><strong>Confidence:</strong> ${pred.confidence}%</span>
        <span><strong>Experience:</strong> ${pred.raw_features.years_experience} yrs</span>
      </div>

      <p class="narration">${pred.narration ?? ""}</p>
      <ul class="shap-list">${shapItems}</ul>

      ${decisionTag}

      <div class="decision-row">
        <input type="text" placeholder="Reason (required)" class="reason-input" ${c.decision ? "disabled" : ""} />
        <button class="small approve" ${c.decision ? "disabled" : ""} data-action="approve">Approve</button>
        <button class="small reject" ${c.decision ? "disabled" : ""} data-action="reject">Reject</button>
        <button class="small modify" ${c.decision ? "disabled" : ""} data-action="modify">Modify Score</button>
      </div>
    </div>
  `;
}

async function refreshCandidates() {
  const res = await fetch(`${API}/api/candidates`);
  const data = await res.json();
  if (!data.candidates.length) {
    candidateList.innerHTML = `<p class="empty-state">No candidates yet — analyze some resumes above.</p>`;
    return;
  }
  candidateList.innerHTML = data.candidates
    .sort((a, b) => b.prediction.fit_score - a.prediction.fit_score)
    .map(renderCandidate)
    .join("");
}

analyzeBtn.addEventListener("click", async () => {
  const files = resumeFilesInput.files;
  if (!files.length) {
    uploadStatus.textContent = "Choose at least one resume PDF first.";
    return;
  }
  const category = categorySelect.value;
  uploadStatus.textContent = `Analyzing ${files.length} resume(s)...`;
  analyzeBtn.disabled = true;

  for (const file of files) {
    const formData = new FormData();
    formData.append("category", category);
    formData.append("file", file);
    try {
      const res = await fetch(`${API}/api/analyze-resume`, { method: "POST", body: formData });
      if (!res.ok) {
        const err = await res.json();
        uploadStatus.textContent = `Error on ${file.name}: ${err.detail}`;
        continue;
      }
    } catch (e) {
      uploadStatus.textContent = `Network error on ${file.name}.`;
    }
  }

  uploadStatus.textContent = "Done.";
  analyzeBtn.disabled = false;
  resumeFilesInput.value = "";
  await refreshCandidates();
});

candidateList.addEventListener("click", async (e) => {
  const action = e.target.dataset.action;
  if (!action) return;

  const card = e.target.closest(".candidate-card");
  const candidateId = card.dataset.id;
  const reasonInput = card.querySelector(".reason-input");
  const reason = reasonInput.value.trim();

  if (!reason) {
    reasonInput.placeholder = "Reason is required!";
    reasonInput.style.borderColor = "var(--weak)";
    return;
  }

  let modifiedScore = null;
  if (action === "modify") {
    modifiedScore = prompt("Enter the recruiter-adjusted fit score (0-100):");
    if (modifiedScore === null) return;
    modifiedScore = parseFloat(modifiedScore);
  }

  await fetch(`${API}/api/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      candidate_id: candidateId,
      decision: action,
      reason,
      modified_score: modifiedScore,
    }),
  });

  await refreshCandidates();
});

reportBtn.addEventListener("click", () => {
  window.open(`${API}/api/report`, "_blank");
});

loadCategories();
refreshCandidates();
