(function () {
  "use strict";

  const form = document.getElementById("analyzeForm");
  const resumeInput = document.getElementById("resumeUpload");
  const dropzone = document.getElementById("dropzone");
  const dzFilename = document.getElementById("dzFilename");
  const formError = document.getElementById("formError");
  const analyzeBtn = document.getElementById("analyzeBtn");

  const resultsEmpty = document.getElementById("resultsEmpty");
  const resultsLoading = document.getElementById("resultsLoading");
  const resultsContent = document.getElementById("resultsContent");
  const loadingText = document.getElementById("loadingText");

  const gaugeFill = document.getElementById("gaugeFill");
  const scoreNumber = document.getElementById("scoreNumber");
  const scoreNote = document.getElementById("scoreNote");
  const matchedSkillsEl = document.getElementById("matchedSkills");
  const missingSkillsEl = document.getElementById("missingSkills");
  const suggestionList = document.getElementById("suggestionList");
  const jdSkillsLine = document.getElementById("jdSkillsLine");
  const jdTermsLine = document.getElementById("jdTermsLine");
  const resumeSkillsLine = document.getElementById("resumeSkillsLine");
  const letterArea = document.getElementById("letterArea");
  const downloadLetterBtn = document.getElementById("downloadLetterBtn");

  const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 84; // r=84

  /* ---------- Dropzone interactions ---------- */
  dropzone.addEventListener("click", () => resumeInput.click());
  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      resumeInput.click();
    }
  });

  resumeInput.addEventListener("change", () => {
    updateDropzoneFile();
  });

  ["dragenter", "dragover"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });
  ["dragleave", "dragend", "drop"].forEach((evt) => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file && file.type === "application/pdf") {
      resumeInput.files = e.dataTransfer.files;
      updateDropzoneFile();
    } else if (file) {
      showError("Please drop a PDF file.");
    }
  });

  function updateDropzoneFile() {
    const file = resumeInput.files && resumeInput.files[0];
    if (file) {
      dzFilename.textContent = `Selected: ${file.name}`;
      dropzone.classList.add("has-file");
    } else {
      dzFilename.textContent = "";
      dropzone.classList.remove("has-file");
    }
  }

  /* ---------- Tabs ---------- */
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => {
        b.classList.toggle("active", b === btn);
        b.setAttribute("aria-selected", b === btn ? "true" : "false");
      });
      tabPanels.forEach((p) => {
        p.hidden = p.dataset.panel !== btn.dataset.tab;
      });
    });
  });

  /* ---------- Error helper ---------- */
  function showError(message) {
    formError.textContent = message;
    if (message) {
      formError.parentElement.classList.add("shake");
      setTimeout(() => formError.parentElement.classList.remove("shake"), 400);
    }
  }

  /* ---------- Loading text rotation ---------- */
  const loadingMessages = [
    "Reading your resume…",
    "Scanning the job description…",
    "Comparing skill sets…",
    "Calculating your ATS score…",
    "Drafting your cover letter…",
  ];
  let loadingInterval = null;
  function startLoadingMessages() {
    let i = 0;
    loadingText.textContent = loadingMessages[0];
    loadingInterval = setInterval(() => {
      i = (i + 1) % loadingMessages.length;
      loadingText.textContent = loadingMessages[i];
    }, 1100);
  }
  function stopLoadingMessages() {
    if (loadingInterval) clearInterval(loadingInterval);
    loadingInterval = null;
  }

  /* ---------- Render helpers ---------- */
  function renderChips(container, items, emptyMessage) {
    container.innerHTML = "";
    if (!items || items.length === 0) {
      const span = document.createElement("span");
      span.className = "chip-empty";
      span.textContent = emptyMessage;
      container.appendChild(span);
      return;
    }
    items.forEach((item, idx) => {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = item;
      chip.style.animationDelay = `${idx * 0.05}s`;
      container.appendChild(chip);
    });
  }

  function renderSuggestions(items) {
    suggestionList.innerHTML = "";
    items.forEach((text, idx) => {
      const li = document.createElement("li");
      li.textContent = text;
      li.style.animationDelay = `${idx * 0.08}s`;
      suggestionList.appendChild(li);
    });
  }

  function animateGauge(score) {
    const clamped = Math.max(0, Math.min(100, score));
    const offset = GAUGE_CIRCUMFERENCE - (clamped / 100) * GAUGE_CIRCUMFERENCE;
    gaugeFill.style.strokeDasharray = `${GAUGE_CIRCUMFERENCE}`;
    gaugeFill.style.strokeDashoffset = `${GAUGE_CIRCUMFERENCE}`;
    // force reflow then animate
    requestAnimationFrame(() => {
      gaugeFill.style.strokeDashoffset = `${offset}`;
    });
    animateNumber(scoreNumber, 0, clamped, 1200);

    if (clamped >= 75) {
      scoreNote.textContent = "Strong match — fine-tune the gaps below and you're ready to apply.";
    } else if (clamped >= 45) {
      scoreNote.textContent = "Decent foundation — closing a few keyword gaps will boost this a lot.";
    } else {
      scoreNote.textContent = "Early stage match — focus on the missing keywords before applying.";
    }
  }

  function animateNumber(el, from, to, duration) {
    const start = performance.now();
    function tick(now) {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(from + (to - from) * eased);
      el.textContent = value;
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  /* ---------- Form submit ---------- */
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("");

    const resumeFile = resumeInput.files && resumeInput.files[0];
    const jdText = document.getElementById("jdText").value.trim();

    if (!resumeFile) {
      showError("Please upload your resume PDF.");
      return;
    }
    if (!jdText) {
      showError("Please paste a job description.");
      return;
    }

    const formData = new FormData(form);

    analyzeBtn.disabled = true;
    resultsEmpty.hidden = true;
    resultsContent.hidden = true;
    resultsLoading.hidden = false;
    startLoadingMessages();

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    try {
      const apiUrl = new URL("/api/analyze", window.location.origin).toString();
      const response = await fetch(apiUrl, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      let data;
      const rawText = await response.text();
      try {
        data = JSON.parse(rawText);
      } catch (parseErr) {
        throw new Error(
          `Server returned an unexpected response (status ${response.status}). ` +
          `Check the terminal running app.py for a Python error.`
        );
      }

      if (!response.ok) {
        throw new Error(data.error || `Request failed with status ${response.status}.`);
      }

      stopLoadingMessages();
      resultsLoading.hidden = true;
      resultsContent.hidden = false;

      animateGauge(data.score);
      renderChips(matchedSkillsEl, data.matched_skills, "No direct skill matches detected yet.");
      renderChips(missingSkillsEl, data.missing_skills, "Great match — no major skill gaps detected.");
      renderSuggestions(data.suggestions);

      jdSkillsLine.textContent = (data.jd_skills && data.jd_skills.join(", ")) || "No known skills detected.";
      jdTermsLine.textContent = (data.jd_terms && data.jd_terms.join(", ")) || "No terms detected.";
      resumeSkillsLine.textContent = (data.resume_skills && data.resume_skills.join(", ")) || "No known skills detected.";

      letterArea.value = data.cover_letter || "";

    } catch (err) {
      clearTimeout(timeoutId);
      stopLoadingMessages();
      resultsLoading.hidden = true;
      resultsEmpty.hidden = false;

      let message;
      if (err.name === "AbortError") {
        message = "The request timed out after 45 seconds. Is the Flask server (python app.py) still running?";
      } else if (err instanceof TypeError) {
        // fetch throws a plain TypeError ("Failed to fetch") when it can't reach the server at all
        message = "Could not reach the server. Make sure 'python app.py' is still running in your terminal, " +
          "then refresh this page and try again. If it keeps happening, a browser extension (ad blocker / shields) " +
          "may be blocking the request — try disabling it for this page.";
      } else {
        message = err.message || "Something went wrong. Please try again.";
      }
      showError(message);
      console.error("CareerCopilot analyze request failed:", err);
    } finally {
      analyzeBtn.disabled = false;
    }
  });

  /* ---------- Download cover letter ---------- */
  downloadLetterBtn.addEventListener("click", () => {
    const text = letterArea.value || "";
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cover_letter.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
})();
