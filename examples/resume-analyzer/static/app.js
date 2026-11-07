// AI Resume & ATS Match Analyzer Dashboard Logic
document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");
  const fileName = document.getElementById("fileName");
  const resumeText = document.getElementById("resumeText");
  const jobTitle = document.getElementById("jobTitle");
  const minExp = document.getElementById("minExp");
  const requiredSkills = document.getElementById("requiredSkills");
  const jobDesc = document.getElementById("jobDesc");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const statusMsg = document.getElementById("statusMsg");
  const resultsCard = document.getElementById("results");

  let selectedFile = null;

  // File Picker & Dropzone Interactions
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      fileInput.click();
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        handleFileSelected(file);
      } else {
        showError("Please select a PDF file.");
      }
    }
  });

  function handleFileSelected(file) {
    selectedFile = file;
    fileName.textContent = `Selected: ${file.name} (${Math.round(file.size / 1024)} KB)`;
    fileName.classList.remove("hidden");
    clearError();
  }

  function showError(msg) {
    statusMsg.textContent = msg;
    statusMsg.className = "status-msg status-error";
    statusMsg.classList.remove("hidden");
  }

  function clearError() {
    statusMsg.textContent = "";
    statusMsg.classList.add("hidden");
  }

  analyzeBtn.addEventListener("click", async () => {
    clearError();
    const textVal = resumeText.value.trim();

    if (!selectedFile && !textVal) {
      showError("Please upload a PDF resume or paste resume text to analyze.");
      return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing in memory...";

    try {
      let response;
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("job_description", jobDesc.value.trim());
        formData.append("title", jobTitle.value.trim());
        formData.append("required_skills_csv", requiredSkills.value.trim());
        formData.append("min_years_experience", minExp.value || "0.0");

        response = await fetch("/api/analyze", {
          method: "POST",
          body: formData,
        });
      } else {
        const payload = {
          resume_text: textVal,
          job_description: jobDesc.value.trim(),
          title: jobTitle.value.trim(),
          required_skills: requiredSkills.value.split(",").map((s) => s.trim()).filter(Boolean),
          min_years_experience: parseFloat(minExp.value) || 0.0,
        };

        response = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Server responded with ${response.status}`);
      }

      const data = await response.json();
      renderResults(data);
    } catch (err) {
      showError(`Analysis failed: ${err.message}`);
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "Run ATS Gauntlet Analysis";
    }
  });

  function renderResults(data) {
    const { score, candidate, skills_analysis } = data;

    // Scores
    document.getElementById("overallScore").textContent = Math.round(score.overall_score);
    document.getElementById("keywordScore").textContent = `${Math.round(score.keyword_match_score)}%`;
    document.getElementById("expScore").textContent = `${Math.round(score.experience_score)}%`;
    document.getElementById("formatScore").textContent = `${Math.round(score.format_score)}%`;

    // Candidate metadata
    const candDiv = document.getElementById("candidateDetails");
    const expText = candidate.experience_years > 0 ? ` • ${candidate.experience_years} yrs exp` : "";
    const emailText = candidate.email ? ` • ${candidate.email}` : "";
    candDiv.textContent = `Candidate: ${candidate.name}${emailText}${expText}`;

    // Badges
    const matchedContainer = document.getElementById("matchedBadges");
    const missingContainer = document.getElementById("missingBadges");
    matchedContainer.innerHTML = "";
    missingContainer.innerHTML = "";

    const matched = score.matching_keywords || [];
    const missing = score.missing_critical_keywords || [];

    document.getElementById("matchedCount").textContent = matched.length;
    document.getElementById("missingCount").textContent = missing.length;

    matched.forEach((skill) => {
      const b = document.createElement("span");
      b.className = "badge badge-matched";
      b.textContent = skill;
      matchedContainer.appendChild(b);
    });

    missing.forEach((skill) => {
      const b = document.createElement("span");
      b.className = "badge badge-missing";
      b.textContent = skill;
      missingContainer.appendChild(b);
    });

    if (matched.length === 0) {
      matchedContainer.innerHTML = '<span style="color:var(--text-muted);font-size:0.85rem;">None detected</span>';
    }
    if (missing.length === 0) {
      missingContainer.innerHTML = '<span style="color:var(--success);font-size:0.85rem;">None! 100% matched</span>';
    }

    // Suggestions
    const suggList = document.getElementById("suggestionsList");
    suggList.innerHTML = "";
    (score.suggestions || []).forEach((sugg) => {
      const li = document.createElement("li");
      li.textContent = sugg;
      suggList.appendChild(li);
    });

    resultsCard.classList.remove("hidden");
    resultsCard.scrollIntoView({ behavior: "smooth" });
  }
});
