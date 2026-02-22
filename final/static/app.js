let sessionId = null;
let selectedMode = "board_investors";
let selectedSubmode = "";
let selectedBoss = "boss_1";

function setActiveButton(selector, activeEl) {
  document.querySelectorAll(selector).forEach((el) => el.classList.remove("active"));
  activeEl.classList.add("active");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function escapeHtml(text) {
  return (text || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function appendChatMessage({ speaker, label, text, status = "", pending = false }) {
  const feed = document.getElementById("chatFeed");
  const item = document.createElement("article");
  item.className = `chat-item ${speaker === "user" ? "chat-user" : "chat-ai"} reveal-pop`;
  if (pending) item.classList.add("chat-pending");
  item.innerHTML = `
    <div class="chat-meta">
      <span class="chat-label">${escapeHtml(label)}</span>
      <span class="chat-status">${escapeHtml(status)}</span>
    </div>
    <p class="chat-text">${escapeHtml(text)}</p>
  `;
  feed.appendChild(item);
  feed.scrollTop = feed.scrollHeight;
  return item;
}

function updatePendingMessage(node, { status = "", text = "", pending = false }) {
  if (!node) return;
  const statusNode = node.querySelector(".chat-status");
  const textNode = node.querySelector(".chat-text");
  if (statusNode) statusNode.textContent = status;
  if (textNode) textNode.textContent = text;
  node.classList.toggle("chat-pending", pending);
}

function renderMockInterview(interview) {
  if (!interview || !Array.isArray(interview.turns)) return "";
  const lines = [];
  if (interview.interview_title) lines.push(`Interview: ${interview.interview_title}`);
  if (interview.scenario) lines.push(`Scenario: ${interview.scenario}`);
  lines.push("");
  for (const turn of interview.turns) {
    lines.push(`${turn.speaker || "Speaker"}: ${turn.message || ""}`);
    lines.push("");
  }
  if (Array.isArray(interview.coach_notes) && interview.coach_notes.length) {
    lines.push("Coach Notes:");
    interview.coach_notes.forEach((note, idx) => lines.push(`${idx + 1}. ${note}`));
  }
  return lines.join("\n").trim();
}

function syncPanels() {
  const bossPanel = document.getElementById("bossPanel");
  const subsections = document.getElementById("subsections");
  const resumeUploadWrap = document.getElementById("resumeUploadWrap");
  const experienceWrap = document.getElementById("experienceWrap");
  const softwareYearsWrap = document.getElementById("softwareYearsWrap");
  const experienceLevel = document.getElementById("experienceLevel");
  const isBoardMode = selectedMode === "board_investors";
  const isInterviewMode = selectedMode === "interview_1on1";
  const isSoftwarePrepSubmode = selectedSubmode === "software_engineer_interview_prep";
  const isSoftwareEngineer = (experienceLevel?.value || "") === "software_engineer";

  bossPanel.style.display = isBoardMode ? "block" : "none";
  subsections.style.display = isInterviewMode ? "flex" : "none";
  resumeUploadWrap.style.display = isInterviewMode && isSoftwarePrepSubmode ? "block" : "none";
  experienceWrap.style.display = isInterviewMode ? "block" : "none";
  softwareYearsWrap.style.display = isInterviewMode && isSoftwareEngineer ? "block" : "none";
}

function setButtonsDisabled(disabled) {
  ["startBtn", "setBossBtn"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.disabled = disabled;
  });
  if (disabled) {
    const sendBtn = document.getElementById("sendBtn");
    const finalizeBtn = document.getElementById("finalizeBtn");
    if (sendBtn) sendBtn.disabled = true;
    if (finalizeBtn) finalizeBtn.disabled = true;
  }
}

function setChatEnabled(enabled) {
  const input = document.getElementById("chatMessage");
  const sendBtn = document.getElementById("sendBtn");
  const finalizeBtn = document.getElementById("finalizeBtn");
  if (input) input.disabled = !enabled;
  if (sendBtn) sendBtn.disabled = !enabled;
  if (finalizeBtn) finalizeBtn.disabled = !enabled;
}

function getSetupPayload() {
  const isInterviewMode = selectedMode === "interview_1on1";
  const experienceLevel = document.getElementById("experienceLevel").value || "";
  const softwareYears = document.getElementById("softwareYears").value || "";
  let codingExperience = "";
  if (isInterviewMode) {
    codingExperience = experienceLevel;
    if (experienceLevel === "software_engineer") {
      codingExperience = `software_engineer_${softwareYears}`;
    }
  }

  return {
    resume_text: document.getElementById("resume").value || "",
    company_context: document.getElementById("companyContext").value || "",
    projects_text: document.getElementById("projectsText").value || "",
    coding_experience_level: codingExperience,
  };
}

async function startSession() {
  setButtonsDisabled(true);
  try {
    const submodeForRequest = selectedMode === "interview_1on1" ? selectedSubmode : "";
    const setup = getSetupPayload();
    const res = await fetch("/api/session/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: selectedMode, submode: submodeForRequest, ...setup }),
    });
    const data = await res.json();
    if (!data.session_id) {
      document.getElementById("sessionInfo").innerText = data.error || "Failed to start session";
      setChatEnabled(false);
      return;
    }

    sessionId = data.session_id;
    selectedBoss = data.selected_boss || "boss_1";
    const bossBtn = document.querySelector(`[data-boss="${selectedBoss}"]`);
    if (bossBtn) setActiveButton(".boss-btn", bossBtn);

    document.getElementById("chatFeed").innerHTML = "";
    document.getElementById("chatMessage").value = "";
    document.getElementById("finalOutputWrap").style.display = "none";
    document.getElementById("finalOutput").textContent = "";
    setChatEnabled(true);

    document.getElementById("sessionInfo").innerText =
      `New session started. Mode: ${selectedMode}${submodeForRequest ? ` | Submode: ${submodeForRequest}` : ""} | Experience: ${setup.coding_experience_level || "not set"}`;

    appendChatMessage({
      speaker: "ai",
      label: "System",
      text: "Session is live. Your setup context is loaded. Start chatting below.",
      status: "ready",
    });
  } catch (err) {
    document.getElementById("sessionInfo").innerText = `Start failed: ${err}`;
    setChatEnabled(false);
  } finally {
    setButtonsDisabled(false);
    setChatEnabled(Boolean(sessionId));
  }
}

async function sendMessage() {
  if (!sessionId) {
    document.getElementById("sessionInfo").innerText = "Start a session first.";
    return;
  }

  const message = (document.getElementById("chatMessage").value || "").trim();
  if (!message) {
    document.getElementById("sessionInfo").innerText = "Enter a message before sending.";
    return;
  }

  const setup = getSetupPayload();
  appendChatMessage({ speaker: "user", label: "You", text: message, status: "sent" });
  document.getElementById("chatMessage").value = "";
  document.getElementById("finalOutputWrap").style.display = "none";
  document.getElementById("finalOutput").textContent = "";

  const pendingNodes = selectedMode === "board_investors"
    ? [
        appendChatMessage({ speaker: "ai", label: "Panel 1", text: "thinking...", status: "thinking", pending: true }),
        appendChatMessage({ speaker: "ai", label: "Panel 2", text: "thinking...", status: "thinking", pending: true }),
        appendChatMessage({ speaker: "ai", label: "Panel 3", text: "thinking...", status: "thinking", pending: true }),
      ]
    : [appendChatMessage({ speaker: "ai", label: "Coach", text: "thinking...", status: "thinking", pending: true })];

  setButtonsDisabled(true);
  try {
    const res = await fetch("/api/session/message/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message, ...setup }),
    });
    const data = await res.json();
    if (!data.ok) {
      pendingNodes.forEach((node) => {
        updatePendingMessage(node, { status: "error", text: data.error || "Request failed", pending: false });
      });
      return;
    }

    const responses = Array.isArray(data.responses) ? data.responses : [];
    for (let i = 0; i < pendingNodes.length; i += 1) {
      const node = pendingNodes[i];
      const response = responses[i];
      updatePendingMessage(node, { status: "speaking", text: "speaking...", pending: true });
      await sleep(220);
      updatePendingMessage(node, {
        status: "done",
        text: response?.message || "No response generated.",
        pending: false,
      });
    }
  } catch (err) {
    pendingNodes.forEach((node) => {
      updatePendingMessage(node, { status: "error", text: `Failed: ${err}`, pending: false });
    });
  } finally {
    setButtonsDisabled(false);
    setChatEnabled(Boolean(sessionId));
  }
}

async function finalizeSession() {
  if (!sessionId) return;
  setButtonsDisabled(true);
  try {
    const finalPending = appendChatMessage({
      speaker: "ai",
      label: "System",
      text: "Finalizing output...",
      status: "thinking",
      pending: true,
    });

    const res = await fetch(`/api/session/${sessionId}/finalize`, { method: "POST" });
    const data = await res.json();
    if (data.error) {
      updatePendingMessage(finalPending, { status: "error", text: data.error, pending: false });
      return;
    }

    updatePendingMessage(finalPending, { status: "done", text: "Final interview output ready.", pending: false });
    document.getElementById("finalOutputWrap").style.display = "block";
    document.getElementById("finalOutput").textContent = renderMockInterview(data.mock_interview) || "No interview output.";
  } finally {
    setButtonsDisabled(false);
    setChatEnabled(Boolean(sessionId));
  }
}

async function setBossPath() {
  if (!sessionId) {
    document.getElementById("sessionInfo").innerText = "Start a session before selecting panel path.";
    return;
  }
  setButtonsDisabled(true);
  try {
    const res = await fetch(`/api/session/${sessionId}/select-boss`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ boss_id: selectedBoss }),
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById("sessionInfo").innerText = `Panel path applied: ${data.selected_boss}`;
      appendChatMessage({
        speaker: "ai",
        label: "System",
        text: `Board path switched to ${data.selected_boss}.`,
        status: "updated",
      });
    }
  } finally {
    setButtonsDisabled(false);
    setChatEnabled(Boolean(sessionId));
  }
}

const modeSelect = document.getElementById("modeSelect");
if (modeSelect) {
  selectedMode = modeSelect.value;
  modeSelect.addEventListener("change", () => {
    selectedMode = modeSelect.value;
    syncPanels();
  });
}

document.querySelectorAll(".submode-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    selectedSubmode = btn.dataset.submode || "";
    setActiveButton(".submode-btn", btn);
  });
});

document.querySelectorAll(".boss-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    selectedBoss = btn.dataset.boss;
    setActiveButton(".boss-btn", btn);
  });
});

document.getElementById("startBtn").addEventListener("click", startSession);
document.getElementById("setBossBtn").addEventListener("click", setBossPath);
document.getElementById("sendBtn").addEventListener("click", sendMessage);
document.getElementById("finalizeBtn").addEventListener("click", finalizeSession);
document.getElementById("experienceLevel").addEventListener("change", syncPanels);
document.getElementById("chatMessage").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});
document.getElementById("resumeFile").addEventListener("change", async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  const lower = file.name.toLowerCase();
  if (!lower.endsWith(".txt") && !lower.endsWith(".md")) {
    appendChatMessage({
      speaker: "ai",
      label: "System",
      text: "Unsupported resume format. Use .txt or .md, or paste text directly.",
      status: "error",
    });
    return;
  }
  const text = await file.text();
  document.getElementById("resume").value = text;
  appendChatMessage({
    speaker: "ai",
    label: "System",
    text: `Resume loaded: ${file.name}`,
    status: "ready",
  });
});

setChatEnabled(false);
syncPanels();
