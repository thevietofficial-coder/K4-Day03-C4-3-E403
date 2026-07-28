const chatWindow = document.getElementById("chatWindow");
const composerForm = document.getElementById("composerForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const modeToggle = document.getElementById("modeToggle");
const resetBtn = document.getElementById("resetBtn");

let currentMode = "agent";

resetBtn.addEventListener("click", async () => {
  if (isSending) return;
  resetBtn.disabled = true;
  await fetch("/api/reset", { method: "POST" });
  resetBtn.disabled = false;
  chatWindow.innerHTML = `
    <div class="msg msg-assistant">
      <div class="msg-avatar">🏠</div>
      <div class="msg-bubble">🔄 Đã bắt đầu phiên trò chuyện mới — bộ nhớ hội thoại đã được xoá.</div>
    </div>
  `;
});

modeToggle.addEventListener("click", (e) => {
  const btn = e.target.closest(".mode-btn");
  if (!btn) return;
  document.querySelectorAll(".mode-btn").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  currentMode = btn.dataset.mode;
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function scrollToBottom() {
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function addUserMessage(text) {
  const el = document.createElement("div");
  el.className = "msg msg-user";
  el.innerHTML = `
    <div class="msg-avatar">🧑</div>
    <div class="msg-bubble">${escapeHtml(text)}</div>
  `;
  chatWindow.appendChild(el);
  scrollToBottom();
}

function addTypingIndicator() {
  const el = document.createElement("div");
  el.className = "msg msg-assistant";
  el.id = "typingIndicator";
  el.innerHTML = `
    <div class="msg-avatar">🏠</div>
    <div class="msg-bubble typing-dots"><span></span><span></span><span></span></div>
  `;
  chatWindow.appendChild(el);
  scrollToBottom();
}

function removeTypingIndicator() {
  const el = document.getElementById("typingIndicator");
  if (el) el.remove();
}

function renderTraceStep(step) {
  const wrap = document.createElement("div");
  wrap.className = "trace-step";

  if (step.type === "action") {
    wrap.innerHTML = `
      <div class="step-label">Bước ${step.step}</div>
      <div class="thought">🧠 ${escapeHtml(step.thought)}</div>
      <div class="action-line">🛠️ ${escapeHtml(step.tool)}[${escapeHtml(step.args)}]</div>
      <div class="observation">👁️ ${escapeHtml(step.observation)}</div>
    `;
  } else if (step.type === "invalid") {
    wrap.innerHTML = `
      <div class="step-label">Bước ${step.step} — Định dạng không hợp lệ</div>
      <div class="observation">⚠️ ${escapeHtml(step.observation)}</div>
    `;
  } else if (step.type === "final") {
    wrap.innerHTML = `
      <div class="step-label">Bước ${step.step} — Kết luận</div>
      <div class="thought">🧠 ${escapeHtml(step.thought)}</div>
    `;
  } else if (step.type === "guardrail") {
    wrap.innerHTML = `
      <div class="step-label">🛡️ Guardrail kích hoạt</div>
      <div class="observation">Đã chạm giới hạn số bước tối đa — vòng lặp bị ngắt an toàn.</div>
    `;
  }
  return wrap;
}

function addAssistantMessage({ tagText, tagClass, bodyText, trace, plan }) {
  const el = document.createElement("div");
  el.className = "msg msg-assistant" + (tagClass === "tag-agent" ? " msg-agent" : "");

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  const tag = document.createElement("span");
  tag.className = "msg-tag " + tagClass;
  tag.textContent = tagText;
  bubble.appendChild(tag);

  if (plan) {
    const planBox = document.createElement("div");
    planBox.className = "plan-box";
    planBox.innerHTML = `<span class="plan-label">🗺️ Kế hoạch (Planning)</span>`;
    const planText = document.createElement("div");
    planText.textContent = plan;
    planBox.appendChild(planText);
    bubble.appendChild(planBox);
  }

  const body = document.createElement("div");
  body.textContent = bodyText;
  bubble.appendChild(document.createElement("br"));
  bubble.appendChild(body);

  if (trace && trace.length) {
    const toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.className = "trace-toggle";
    toggleBtn.textContent = `🔍 Xem quá trình suy luận (${trace.length} bước)`;

    const panel = document.createElement("div");
    panel.className = "trace-panel";
    trace.forEach((step) => panel.appendChild(renderTraceStep(step)));

    toggleBtn.addEventListener("click", () => {
      panel.classList.toggle("open");
      toggleBtn.textContent = panel.classList.contains("open")
        ? "🔼 Ẩn quá trình suy luận"
        : `🔍 Xem quá trình suy luận (${trace.length} bước)`;
      scrollToBottom();
    });

    bubble.appendChild(toggleBtn);
    bubble.appendChild(panel);
  }

  el.innerHTML = `<div class="msg-avatar">🏠</div>`;
  el.appendChild(bubble);
  chatWindow.appendChild(el);
  scrollToBottom();
}

let isSending = false;

async function sendMessage(message) {
  if (isSending) return;
  isSending = true;

  addUserMessage(message);
  addTypingIndicator();
  sendBtn.disabled = true;
  messageInput.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, mode: currentMode }),
    });
    const data = await res.json();
    removeTypingIndicator();

    if (!res.ok) {
      addAssistantMessage({
        tagText: "Lỗi",
        tagClass: "tag-guardrail",
        bodyText: data.error || "Đã có lỗi xảy ra.",
      });
      return;
    }

    if (data.baseline) {
      addAssistantMessage({
        tagText: "Chatbot Baseline",
        tagClass: "tag-baseline",
        bodyText: data.baseline.response,
      });
    }

    if (data.agent) {
      addAssistantMessage({
        tagText: data.agent.guardrail_triggered ? "ReAct Agent · Guardrail" : "ReAct Agent",
        tagClass: data.agent.guardrail_triggered ? "tag-guardrail" : "tag-agent",
        bodyText: data.agent.final_answer,
        trace: data.agent.trace,
        plan: data.agent.plan,
      });
    }
  } catch (err) {
    removeTypingIndicator();
    addAssistantMessage({
      tagText: "Lỗi kết nối",
      tagClass: "tag-guardrail",
      bodyText: "Không thể kết nối tới server. Vui lòng thử lại.",
    });
  } finally {
    isSending = false;
    sendBtn.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
  }
}

composerForm.addEventListener("submit", (e) => {
  e.preventDefault();
  if (isSending) return;
  const text = messageInput.value.trim();
  if (!text) return;
  messageInput.value = "";
  sendMessage(text);
});

messageInput.focus();
