const promptInput = document.getElementById("prompt-input");
const generateBtn = document.getElementById("generate-btn");
const emptyState = document.getElementById("empty-state");
const messageFeed = document.getElementById("message-feed");
const chatScroll = document.getElementById("chat-scroll");
const historyList = document.getElementById("history-list");
const newBtn = document.getElementById("new-btn");
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebar-toggle");
const tierButtons = document.querySelectorAll(".tier-btn");
const creditsDisplay = document.querySelector(".credits-remaining");

let currentTier = "standard";

tierButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    currentTier = btn.dataset.tier;
    tierButtons.forEach((b) => b.classList.toggle("is-active", b === btn));
  });
});

// ---- Auto-resize the textarea as the person types ----
promptInput.addEventListener("input", () => {
  promptInput.style.height = "auto";
  promptInput.style.height = Math.min(promptInput.scrollHeight, 140) + "px";
});

promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    generateImage();
  }
});

generateBtn.addEventListener("click", generateImage);

function scrollToBottom() {
  chatScroll.scrollTo({ top: chatScroll.scrollHeight, behavior: "smooth" });
}

async function generateImage() {
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  emptyState.style.display = "none";
  generateBtn.disabled = true;
  promptInput.value = "";
  promptInput.style.height = "auto";

  // ---- Append the user's message bubble immediately ----
  const pair = document.createElement("div");
  pair.className = "message-pair";
  pair.innerHTML = `
    <div class="user-bubble"></div>
    <div class="result-block">
      <div class="result-frame is-loading"></div>
    </div>
  `;
  pair.querySelector(".user-bubble").textContent = prompt;
  messageFeed.appendChild(pair);
  scrollToBottom();

  const resultFrame = pair.querySelector(".result-frame");
  const resultBlock = pair.querySelector(".result-block");

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, tier: currentTier }),
    });

    const data = await response.json();
    if (!response.ok) {
      if (data.requires_login) {
        window.location.href = "/login";
        return;
      }
      if (data.requires_upgrade) {
        window.location.href = "/upgrade";
        return;
      }
      if (data.requires_credits) {
        window.location.href = "/upgrade";
        return;
      }
      throw new Error(data.error || "Something went wrong.");
    }

    const img = document.createElement("img");
    img.src = data.image_url;
    img.alt = prompt;

    await new Promise((resolve, reject) => {
      img.onload = resolve;
      img.onerror = reject;
    });

    resultFrame.classList.remove("is-loading");
    resultFrame.appendChild(img);
    requestAnimationFrame(() => img.classList.add("is-visible"));

    const actions = document.createElement("div");
    actions.className = "result-actions";
    actions.innerHTML = `<a class="download-link" download>↓ Download</a>`;
    actions.querySelector(".download-link").href = data.image_url;
    actions.querySelector(".download-link").download = data.image_url.split("/").pop();
    resultBlock.appendChild(actions);

    addToHistory(data.image_url, prompt);

    // Keep the sidebar credit count in sync after a premium generation
    if (data.credits_remaining !== null && data.credits_remaining !== undefined && creditsDisplay) {
      creditsDisplay.textContent = `${data.credits_remaining} credit${data.credits_remaining !== 1 ? "s" : ""} left`;
    }
  } catch (error) {
    resultFrame.classList.remove("is-loading");
    resultFrame.classList.add("is-error");
    resultFrame.textContent = error.message || "Could not develop this print.";
  } finally {
    generateBtn.disabled = false;
    scrollToBottom();
  }
}

function addToHistory(url, prompt) {
  const emptyMsg = historyList.querySelector(".history-empty");
  if (emptyMsg) emptyMsg.remove();

  const item = document.createElement("div");
  item.className = "history-item";
  item.innerHTML = `<img src="${url}" alt=""><span></span>`;
  item.querySelector("span").textContent = prompt;
  item.title = prompt;
  item.addEventListener("click", () => {
    promptInput.value = prompt;
    promptInput.focus();
    if (window.innerWidth <= 860) sidebar.classList.remove("is-open");
  });

  historyList.prepend(item);
}

// ---- New print: clears the feed and shows the welcome state again ----
newBtn.addEventListener("click", () => {
  messageFeed.innerHTML = "";
  emptyState.style.display = "block";
  promptInput.focus();
  if (window.innerWidth <= 860) sidebar.classList.remove("is-open");
});

// ---- Mobile sidebar toggle ----
sidebarToggle.addEventListener("click", () => {
  sidebar.classList.toggle("is-open");
});

// ---- Prompt chips ----
document.querySelectorAll(".prompt-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    promptInput.value = chip.dataset.prompt;
    promptInput.focus();
  });
});

// ---- Load previously generated images into the sidebar on page load ----
async function loadGallery() {
  try {
    const response = await fetch("/gallery");
    const items = await response.json();
    items.forEach((item) => addToHistory(item.url, item.prompt));
  } catch (error) {
    // history is a nice-to-have, not critical
  }
}

loadGallery();