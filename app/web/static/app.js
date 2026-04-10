const instructionInput = document.getElementById("instruction");
const shellInput = document.getElementById("shell");
const dryRunInput = document.getElementById("dryRun");
const confirmRiskyInput = document.getElementById("confirmRisky");
const translationOutput = document.getElementById("translationOutput");
const safetyOutput = document.getElementById("safetyOutput");
const executionOutput = document.getElementById("executionOutput");
const automationOutput = document.getElementById("automationOutput");
const stepsOutput = document.getElementById("stepsOutput");
const historyList = document.getElementById("historyList");
const learnedList = document.getElementById("learnedList");
const approvalsList = document.getElementById("approvalsList");
const refreshHistoryButton = document.getElementById("refreshHistory");
const refreshLearnedButton = document.getElementById("refreshLearned");
const refreshApprovalsButton = document.getElementById("refreshApprovals");
const aiStatus = document.getElementById("aiStatus");
const learnedCount = document.getElementById("learnedCount");
const automationCount = document.getElementById("automationCount");
const pendingApprovalsCount = document.getElementById("pendingApprovalsCount");
const quickPrompts = document.getElementById("quickPrompts");
const commandForm = document.getElementById("commandForm");
const runButton = document.getElementById("runButton");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatAnalysis(result) {
  const commands = (result.translation.actions || [])
    .map((action, index) => `${index + 1}. ${action.description}\n   ${action.commands?.[result.translation.shell] ?? ""}`)
    .join("\n");

  translationOutput.textContent = [
    `Normalized: ${result.translation.normalized_text}`,
    `Confidence: ${Math.round((result.translation.confidence || 0) * 100)}%`,
    commands || "No commands generated.",
    ...(result.translation.notes || []).map((note) => `Note: ${note}`),
  ].join("\n\n");

  const safetyLines = [
    `Safe: ${result.safety.safe}`,
    `Requires confirmation: ${result.safety.requires_confirmation}`,
    `Blocked: ${result.safety.blocked}`,
    `Summary: ${result.safety.summary || ""}`,
    ...(result.safety.issues || []).map(
      (issue) => `${issue.level.toUpperCase()} [${issue.command_index + 1}]: ${issue.reason}\n   ${issue.command}`,
    ),
  ];
  safetyOutput.textContent = safetyLines.join("\n\n");

  if (!result.automation) {
    automationOutput.textContent = "No dedicated automation section was selected for this prompt.";
  } else {
    const steps = (result.automation.steps || [])
      .map((step, index) => `${index + 1}. ${step.description}`)
      .join("\n");
    automationOutput.textContent = [
      `Category: ${result.automation.category}`,
      `Title: ${result.automation.title}`,
      `Summary: ${result.automation.summary}`,
      `Requires browser: ${result.automation.requires_browser}`,
      `Requires admin: ${result.automation.requires_admin}`,
      `Needs confirmation: ${result.automation.requires_confirmation}`,
      steps ? `Steps:\n${steps}` : "Steps: <none>",
    ].join("\n\n");
  }
}

function formatWorkflow(result) {
  formatAnalysis(result.analysis);
  if (!result.execution) {
    executionOutput.textContent = "Execution was skipped because the command was blocked or confirmation is required.";
    stepsOutput.textContent = "No steps executed.";
    return;
  }

  executionOutput.textContent = [
    `Message: ${result.execution.message}`,
    `Executed: ${result.execution.executed}`,
    `Return code: ${result.execution.return_code ?? "n/a"}`,
    `Shell: ${result.execution.shell}`,
    `Command:\n${result.execution.command}`,
    result.execution.stdout ? `STDOUT:\n${result.execution.stdout}` : "STDOUT: <empty>",
    result.execution.stderr ? `STDERR:\n${result.execution.stderr}` : "STDERR: <empty>",
  ].join("\n\n");

  const steps = (result.execution.steps || [])
    .map((step, index) => {
      return [
        `${index + 1}. ${step.command}`,
        `return_code: ${step.return_code ?? "n/a"}`,
        step.stdout ? `stdout:\n${step.stdout}` : "stdout: <empty>",
        step.stderr ? `stderr:\n${step.stderr}` : "stderr: <empty>",
      ].join("\n");
    })
    .join("\n\n");
  stepsOutput.textContent = steps || "No step data available.";
}

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const payload = await response.json();
  if (!response.ok) {
    const detail = payload?.detail ?? "Request failed.";
    throw new Error(detail);
  }
  return payload;
}

async function refreshHistory() {
  const response = await fetch("/api/history");
  const payload = await response.json();
  const items = payload.items || [];
  historyList.innerHTML = items.length
    ? items
        .map((item) => {
          const time = new Date(item.timestamp * 1000).toLocaleString();
          return `
            <article class="history-item">
              <div class="meta">
                <span class="pill">${item.type}</span>
                <span>${time}</span>
                <span>${item.shell}</span>
              </div>
              <strong>${item.instruction}</strong>
              <pre>${JSON.stringify(item.result, null, 2)}</pre>
            </article>
          `;
        })
        .join("")
    : '<div class="history-item"><strong>No history yet.</strong><pre>Run or analyze a command to populate this section.</pre></div>';
}

async function refreshLearned() {
  const response = await fetch("/api/learned");
  const payload = await response.json();
  const items = payload.items || [];
  learnedList.innerHTML = items.length
    ? items
        .slice(0, 10)
        .map((item) => {
          return `
            <article class="history-item">
              <div class="meta">
                <span class="pill">${item.shell}</span>
                <span>successes: ${item.success_count}</span>
              </div>
              <strong>${item.instruction}</strong>
              <pre>${(item.commands || []).join("\n")}</pre>
            </article>
          `;
        })
        .join("")
    : '<div class="history-item"><strong>No learned commands yet.</strong><pre>Run successful commands in live mode to build adaptive memory.</pre></div>';
}

async function refreshCapabilities() {
  const response = await fetch("/api/capabilities");
  const payload = await response.json();
  aiStatus.textContent = payload.ai_available ? "Enabled" : "Fallback mode";
  learnedCount.textContent = String(payload.learned_count ?? 0);
  automationCount.textContent = String((payload.automation_categories || []).length);
  pendingApprovalsCount.textContent = String(payload.pending_approvals ?? 0);
}

function renderApprovalCard(approval) {
  const steps = (approval.steps || [])
    .map((step) => {
      const commandLine = step.command || "<browser or external step>";
      return `<li><strong>${escapeHtml(step.index + 1)}. ${escapeHtml(step.description)}</strong><pre>${escapeHtml(commandLine)}\nreview: ${step.requires_review ? "yes" : "no"}\napproved: ${step.approved ? "yes" : "no"}</pre></li>`;
    })
    .join("");

  const safeStepIndexes = (approval.steps || [])
    .filter((step) => step.requires_review)
    .map((step) => step.index)
    .join(",");

  return `
    <article class="history-item approval-card" data-approval-id="${approval.id}">
      <div class="meta">
        <span class="pill">${escapeHtml(approval.status)}</span>
        <span>${escapeHtml(approval.shell)}</span>
        <span>${escapeHtml(approval.profile)}</span>
      </div>
      <strong>${escapeHtml(approval.instruction)}</strong>
      <pre>${escapeHtml(approval.summary || "No summary available.")}</pre>
      <pre>${escapeHtml((approval.reason || "").trim() || "No approval reason recorded.")}</pre>
      <div class="approval-actions">
        <label>
          <span>Step indexes</span>
          <input class="approval-step-input" type="text" value="${safeStepIndexes}" placeholder="0,1,2">
        </label>
        <label class="toggle approval-toggle">
          <input class="approval-execute" type="checkbox" ${approval.dry_run ? "" : "checked"}>
          <span>Dry run after approval</span>
        </label>
        <div class="approval-buttons">
          <button type="button" class="primary approval-approve">Approve</button>
          <button type="button" class="secondary approval-deny">Deny</button>
        </div>
      </div>
      <details class="approval-steps">
        <summary>Review steps (${(approval.steps || []).length})</summary>
        <ul>${steps || "<li><strong>No step details.</strong><pre>Approval was created without step metadata.</pre></li>"}</ul>
      </details>
    </article>
  `;
}

async function postApprovalAction(approvalId, action, body) {
  const response = await fetch(`/api/approvals/${approvalId}/${action}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    const detail = payload?.detail ?? "Request failed.";
    throw new Error(detail);
  }
  return payload;
}

async function refreshApprovals() {
  const response = await fetch("/api/approvals?status=pending");
  const payload = await response.json();
  const items = payload.items || [];
  approvalsList.innerHTML = items.length
    ? items.map(renderApprovalCard).join("")
    : '<div class="history-item"><strong>No approvals pending.</strong><pre>Tasks that need review will appear here.</pre></div>';
}

approvalsList.addEventListener("click", async (event) => {
  const card = event.target.closest(".approval-card");
  if (!card) {
    return;
  }

  const approvalId = card.getAttribute("data-approval-id");
  const stepsInput = card.querySelector(".approval-step-input");
  const executeInput = card.querySelector(".approval-execute");

  if (event.target.closest(".approval-approve")) {
    try {
      await postApprovalAction(approvalId, "approve", {
        step_indexes: (stepsInput?.value || "")
          .split(",")
          .map((value) => Number(value.trim()))
          .filter((value) => Number.isInteger(value)),
        execute_after: Boolean(executeInput?.checked),
        dry_run: Boolean(executeInput?.checked),
      });
      await refreshApprovals();
      await refreshHistory();
      await refreshCapabilities();
    } catch (error) {
      executionOutput.textContent = error.message;
    }
  }

  if (event.target.closest(".approval-deny")) {
    try {
      await postApprovalAction(approvalId, "deny", {
        reason: "Denied from dashboard",
      });
      await refreshApprovals();
      await refreshHistory();
      await refreshCapabilities();
    } catch (error) {
      executionOutput.textContent = error.message;
    }
  }
});

async function analyzeOnly(event) {
  event.preventDefault();
  const instruction = instructionInput.value.trim();
  if (!instruction) {
    translationOutput.textContent = "Enter an instruction first.";
    return;
  }

  try {
    const result = await postJson("/api/analyze", {
      instruction,
      shell: shellInput.value,
    });
    formatAnalysis(result);
    executionOutput.textContent = "Analysis completed. Use Run to execute the command.";
    stepsOutput.textContent = "No execution steps yet. Run the command to see step-by-step output.";
    await refreshHistory();
    await refreshLearned();
    await refreshCapabilities();
  } catch (error) {
    executionOutput.textContent = error.message;
  }
}

async function runCommand() {
  const instruction = instructionInput.value.trim();
  if (!instruction) {
    executionOutput.textContent = "Enter an instruction first.";
    return;
  }

  try {
    const result = await postJson("/api/run", {
      instruction,
      shell: shellInput.value,
      confirm_risky: confirmRiskyInput.checked,
      dry_run: dryRunInput.checked,
    });
    formatWorkflow(result);
    await refreshHistory();
    await refreshLearned();
    await refreshCapabilities();
  } catch (error) {
    executionOutput.textContent = error.message;
  }
}

commandForm.addEventListener("submit", analyzeOnly);
runButton.addEventListener("click", runCommand);
refreshHistoryButton.addEventListener("click", refreshHistory);
refreshLearnedButton.addEventListener("click", refreshLearned);
refreshApprovalsButton.addEventListener("click", refreshApprovals);

quickPrompts.addEventListener("click", (event) => {
  const button = event.target.closest(".quick-prompt");
  if (!button) {
    return;
  }
  instructionInput.value = button.getAttribute("data-prompt") || "";
  instructionInput.focus();
});

Promise.all([refreshHistory(), refreshLearned(), refreshApprovals(), refreshCapabilities()]).catch(() => {
  historyList.innerHTML = '<div class="history-item"><strong>History unavailable.</strong><pre>The API is not responding.</pre></div>';
  learnedList.innerHTML = '<div class="history-item"><strong>Learning unavailable.</strong><pre>The API is not responding.</pre></div>';
  approvalsList.innerHTML = '<div class="history-item"><strong>Approvals unavailable.</strong><pre>The API is not responding.</pre></div>';
  aiStatus.textContent = "Unavailable";
  learnedCount.textContent = "-";
  automationCount.textContent = "-";
  pendingApprovalsCount.textContent = "-";
});
