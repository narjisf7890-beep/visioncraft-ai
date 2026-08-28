const promptInput = document.getElementById("prompt-input");
const generateBtn = document.getElementById("generate-btn");
const statusLine = document.getElementById("status-line");
const resultImage = document.getElementById("result-image");
const resultVideo = document.getElementById("result-video");
const placeholder = document.getElementById("print-placeholder");
const veil = document.getElementById("developing-veil");
const caption = document.getElementById("print-caption");
const downloadLink = document.getElementById("download-link");
const sheetStrip = document.getElementById("sheet-strip");
const tabImage = document.getElementById("tab-image");
const tabVideo = document.getElementById("tab-video");
const videoNote = document.getElementById("video-note");

let currentMode = "image"; // "image" or "video"

function setStatus(text, mode) {
  statusLine.textContent = text;
  statusLine.classList.remove("is-active", "is-error");
  if (mode) statusLine.classList.add(mode);
}

function setMode(mode) {
  currentMode = mode;
  tabImage.classList.toggle("is-active", mode === "image");
  tabVideo.classList.toggle("is-active", mode === "video");
  videoNote.classList.toggle("is-visible", mode === "video");
  setStatus("awaiting exposure", null);
}

tabImage.addEventListener("click", () => setMode("image"));
tabVideo.addEventListener("click", () => setMode("video"));

function resetPrintArea() {
  resultImage.classList.remove("is-visible");
  resultVideo.classList.remove("is-visible");
  resultVideo.pause();
  veil.classList.remove("is-developing");
  placeholder.style.display = "none";
  veil.style.display = "block";
  downloadLink.style.display = "none";
}

async function generateImage() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("write a description first", "is-error");
    return;
  }

  generateBtn.disabled = true;
  setStatus("sending exposure to the lab...", "is-active");
  resetPrintArea();

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong.");

    await new Promise((resolve, reject) => {
      resultImage.onload = resolve;
      resultImage.onerror = reject;
      resultImage.src = data.image_url;
    });

    resultImage.classList.add("is-visible");
    requestAnimationFrame(() => veil.classList.add("is-developing"));

    setStatus("print developed", null);
    caption.textContent = `"${data.prompt}"`;
    downloadLink.href = data.image_url;
    downloadLink.download = data.image_url.split("/").pop();
    downloadLink.style.display = "inline-flex";
    addToContactSheet(data.image_url, "image");
  } catch (error) {
    setStatus(error.message || "could not develop this print", "is-error");
    placeholder.style.display = "flex";
    veil.style.display = "none";
  } finally {
    generateBtn.disabled = false;
  }
}

async function generateVideo() {
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("write a description first", "is-error");
    return;
  }

  generateBtn.disabled = true;
  setStatus("developing source frame...", "is-active");
  resetPrintArea();

  const patienceTimer = setTimeout(() => {
    setStatus("still animating — free service, can take a minute...", "is-active");
  }, 8000);

  try {
    const response = await fetch("/generate-video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong.");

    await new Promise((resolve, reject) => {
      resultVideo.onloadeddata = resolve;
      resultVideo.onerror = reject;
      resultVideo.src = data.video_url;
    });

    resultVideo.classList.add("is-visible");
    veil.classList.add("is-developing");
    resultVideo.play();

    setStatus("clip developed", null);
    caption.textContent = `"${data.prompt}"`;
    downloadLink.href = data.video_url;
    downloadLink.download = data.video_url.split("/").pop();
    downloadLink.style.display = "inline-flex";
    addToContactSheet(data.video_url, "video");
  } catch (error) {
    setStatus(error.message || "could not develop this clip", "is-error");
    placeholder.style.display = "flex";
    veil.style.display = "none";
  } finally {
    clearTimeout(patienceTimer);
    generateBtn.disabled = false;
  }
}

async function generate() {
  if (currentMode === "image") {
    await generateImage();
  } else {
    await generateVideo();
  }
}

function addToContactSheet(url, kind) {
  const emptyMsg = sheetStrip.querySelector(".sheet-empty");
  if (emptyMsg) emptyMsg.remove();

  const thumb = document.createElement(kind === "video" ? "div" : "img");
  if (kind === "video") {
    thumb.classList.add("is-video-tile");
    thumb.textContent = "▶";
  } else {
    thumb.src = url;
    thumb.alt = "Previously generated image";
  }

  thumb.addEventListener("click", () => {
    if (kind === "video") {
      resultImage.classList.remove("is-visible");
      resultVideo.src = url;
      resultVideo.classList.add("is-visible");
      resultVideo.play();
      setMode("video");
    } else {
      resultVideo.classList.remove("is-visible");
      resultVideo.pause();
      resultImage.src = url;
      resultImage.classList.add("is-visible");
      setMode("image");
    }
  });

  sheetStrip.prepend(thumb);
}

generateBtn.addEventListener("click", generate);
promptInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") generate();
});

async function loadGallery() {
  try {
    const response = await fetch("/gallery");
    const urls = await response.json();
    if (urls.length > 0) {
      sheetStrip.innerHTML = "";
      urls.forEach((url) => addToContactSheet(url, "image"));
    }
  } catch (error) {
    // gallery is a nice-to-have, not critical
  }
}
// ---- Prompt chips: clicking one fills the input and focuses it ----
document.querySelectorAll(".prompt-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    promptInput.value = chip.dataset.prompt;
    promptInput.focus();
  });
});

// ---- Scroll-reveal: fade sections in as they enter the viewport ----
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-revealed");
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.15 }
);

document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));

loadGallery();