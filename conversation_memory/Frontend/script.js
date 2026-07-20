/**
 * script.js
 * ---------
 * All frontend logic: no frameworks, just the Fetch API + DOM.
 *
 * Responsibilities:
 * 1. User identification via localStorage (crypto.randomUUID(), persisted).
 * 2. Session (conversation) management: create, list, switch, delete.
 * 3. Talking to the FastAPI backend (/chat, /sessions, /chat-history, /new-session, /chat DELETE).
 * 4. Rendering messages, a typing indicator, and the session sidebar.
 *
 * Connects to:
 * - backend/main.py -> every fetch() call below hits one of its routes.
 * - index.html       -> queries elements by the ids defined there.
 * - style.css         -> classes referenced here match the selectors there.
 */

// Change this if your backend runs somewhere other than localhost:8000.
const API_BASE_URL = "http://localhost:8000";

const LOCAL_STORAGE_USER_KEY = "memory_chat_user_id";

// ---------------------------------------------------------------------------
// 1. User identification (no login, no backend involvement)
// ---------------------------------------------------------------------------

function getOrCreateUserId() {
  let userId = localStorage.getItem(LOCAL_STORAGE_USER_KEY);
  if (!userId) {
    userId = crypto.randomUUID();
    localStorage.setItem(LOCAL_STORAGE_USER_KEY, userId);
  }
  return userId;
}

const userId = getOrCreateUserId();

// ---------------------------------------------------------------------------
// App state
// ---------------------------------------------------------------------------

let currentSessionId = null;
let sessions = []; // list of session_id strings for this user

// ---------------------------------------------------------------------------
// DOM references
// ---------------------------------------------------------------------------

const sidebarEl = document.getElementById("sidebar");
const sidebarToggleBtn = document.getElementById("sidebarToggle");
const sessionListEl = document.getElementById("sessionList");
const newChatBtn = document.getElementById("newChatBtn");
const userIdBadge = document.getElementById("userIdBadge");

const chatScrollEl = document.getElementById("chatScroll");
const messagesEl = document.getElementById("messages");
const emptyStateEl = document.getElementById("emptyState");

const composerForm = document.getElementById("composerForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

async function init() {
  userIdBadge.textContent = `user: ${userId.slice(0, 8)}…`;
  userIdBadge.title = `Full id (stored in localStorage): ${userId}`;

  await refreshSessionList();

  if (sessions.length > 0) {
    await switchToSession(sessions[0]);
  } else {
    await startNewChat();
  }

  autoResizeTextarea();
}

// ---------------------------------------------------------------------------
// 2. Session management
// ---------------------------------------------------------------------------

async function refreshSessionList() {
  try {
    const res = await fetch(`${API_BASE_URL}/sessions/${userId}`);
    if (!res.ok) throw new Error("Failed to load sessions");
    sessions = await res.json();
  } catch (err) {
    console.error(err);
    sessions = [];
  }
  renderSessionList();
}

function renderSessionList() {
  sessionListEl.innerHTML = "";

  if (sessions.length === 0) {
    const empty = document.createElement("div");
    empty.className = "session-list-empty";
    empty.textContent = "No conversations yet.";
    sessionListEl.appendChild(empty);
    return;
  }

  sessions.forEach((sessionId, index) => {
    const item = document.createElement("div");
    item.className = "session-item" + (sessionId === currentSessionId ? " active" : "");

    const label = document.createElement("button");
    label.className = "session-item-label";
    label.textContent = `Chat ${index + 1}`;
    label.title = sessionId;
    label.addEventListener("click", () => switchToSession(sessionId));

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "session-delete-btn";
    deleteBtn.setAttribute("aria-label", "Delete conversation");
    deleteBtn.innerHTML =
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteSession(sessionId);
    });

    item.appendChild(label);
    item.appendChild(deleteBtn);
    sessionListEl.appendChild(item);
  });
}

async function startNewChat() {
  // The frontend is the source of truth for id generation per the spec,
  // so we generate the session_id client-side. (POST /new-session also
  // exists on the backend if you'd rather have the server mint ids.)
  const newSessionId = crypto.randomUUID();
  sessions.unshift(newSessionId);
  currentSessionId = newSessionId;
  renderSessionList();
  renderMessages([]);
  closeSidebarOnMobile();
  messageInput.focus();
}

async function switchToSession(sessionId) {
  currentSessionId = sessionId;
  renderSessionList();
  closeSidebarOnMobile();

  try {
    const res = await fetch(`${API_BASE_URL}/chat-history/${userId}/${sessionId}`);
    const history = res.ok ? await res.json() : [];
    renderMessages(history);
  } catch (err) {
    console.error(err);
    renderMessages([]);
  }
}

async function deleteSession(sessionId) {
  try {
    await fetch(`${API_BASE_URL}/chat/${userId}/${sessionId}`, { method: "DELETE" });
  } catch (err) {
    console.error(err);
  }

  sessions = sessions.filter((id) => id !== sessionId);
  renderSessionList();

  if (sessionId === currentSessionId) {
    if (sessions.length > 0) {
      await switchToSession(sessions[0]);
    } else {
      await startNewChat();
    }
  }
}

// ---------------------------------------------------------------------------
// 3. Rendering messages
// ---------------------------------------------------------------------------

function renderMessages(history) {
  messagesEl.innerHTML = "";
  emptyStateEl.style.display = history.length === 0 ? "flex" : "none";
  history.forEach((turn) => appendMessageBubble(turn.role, turn.content));
  scrollToBottom();
}

function appendMessageBubble(role, content) {
  emptyStateEl.style.display = "none";

  const row = document.createElement("div");
  row.className = `message-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = `avatar ${role}`;
  avatar.textContent = role === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
  return row;
}

function showTypingIndicator() {
  const row = document.createElement("div");
  row.className = "message-row assistant";
  row.id = "typingRow";

  const avatar = document.createElement("div");
  avatar.className = "avatar assistant";
  avatar.textContent = "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollToBottom();
}

function removeTypingIndicator() {
  const row = document.getElementById("typingRow");
  if (row) row.remove();
}

function scrollToBottom() {
  chatScrollEl.scrollTop = chatScrollEl.scrollHeight;
}

// ---------------------------------------------------------------------------
// 4. Sending messages
// ---------------------------------------------------------------------------

async function sendMessage(text) {
  appendMessageBubble("user", text);
  showTypingIndicator();
  setComposerEnabled(false);

  try {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        session_id: currentSessionId,
        message: text,
      }),
    });

    removeTypingIndicator();

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      appendMessageBubble(
        "assistant",
        `Something went wrong: ${errBody.detail || res.statusText}`
      );
      return;
    }

    const data = await res.json();
    appendMessageBubble("assistant", data.response);

    // First message in a brand-new session -> it just became a "real"
    // session on the backend, so refresh the list to keep labels in sync.
    if (!sessions.includes(currentSessionId)) {
      sessions.unshift(currentSessionId);
    }
    renderSessionList();
  } catch (err) {
    removeTypingIndicator();
    appendMessageBubble("assistant", "Couldn't reach the server. Is the backend running?");
    console.error(err);
  } finally {
    setComposerEnabled(true);
    messageInput.focus();
  }
}

function setComposerEnabled(enabled) {
  messageInput.disabled = !enabled;
  sendBtn.disabled = !enabled;
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

newChatBtn.addEventListener("click", startNewChat);

composerForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;
  messageInput.value = "";
  autoResizeTextarea();
  sendMessage(text);
});

messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    composerForm.requestSubmit();
  }
});

messageInput.addEventListener("input", autoResizeTextarea);

function autoResizeTextarea() {
  messageInput.style.height = "auto";
  messageInput.style.height = Math.min(messageInput.scrollHeight, 160) + "px";
}

sidebarToggleBtn.addEventListener("click", () => {
  sidebarEl.classList.toggle("open");
});

function closeSidebarOnMobile() {
  sidebarEl.classList.remove("open");
}

// ---------------------------------------------------------------------------
// Go
// ---------------------------------------------------------------------------

init();
