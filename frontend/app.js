let currentDocument = null;

const fileInput = document.getElementById("fileInput");
const dropZone = document.getElementById("dropZone");
const processBtn = document.getElementById("processBtn");
const language = document.getElementById("language");
const statusBox = document.getElementById("status");

dropZone.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  updateSelectedFile();
});

["dragenter", "dragover"].forEach(eventName => {
  dropZone.addEventListener(eventName, e => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach(eventName => {
  dropZone.addEventListener(eventName, e => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", e => {
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    updateSelectedFile();
  }
});

function updateSelectedFile() {
  if (fileInput.files.length) {
    statusBox.textContent = `Selected: ${fileInput.files[0].name}`;
    processBtn.disabled = false;
  } else {
    processBtn.disabled = true;
  }
}

processBtn.addEventListener("click", async () => {
  if (!fileInput.files.length) return;

  processBtn.disabled = true;
  statusBox.textContent = "Processing document. OCR may take some time...";

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("language", language.value);

  try {
    const response = await fetch("/api/process", {
      method: "POST",
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.details || data.error || "Processing failed.");
    }

    currentDocument = data;
    renderResult(data);
    await loadHistory();

    statusBox.textContent = "Document processed successfully.";
  } catch (error) {
    statusBox.textContent = `Error: ${error.message}`;
  } finally {
    processBtn.disabled = false;
  }
});

function renderResult(data) {
  document.getElementById("resultSection").classList.remove("hidden");

  document.getElementById("resultLanguage").textContent =
    languageName(data.language);

  document.getElementById("resultConfidence").textContent =
    `${(data.confidence * 100).toFixed(1)}%`;

  const detections = (data.pages || []).reduce(
    (sum, page) => sum + (page.detections || 0), 0
  );

  document.getElementById("resultDetections").textContent = detections;

  fetch("/api/health")
    .then(r => r.json())
    .then(health => {
      document.getElementById("resultDatabase").textContent = health.database;
    });

  const fields = document.getElementById("fields");
  fields.innerHTML = "";

  const labels = {
    name: "Name",
    address: "Address",
    phone: "Phone",
    email: "Email",
    date: "Date",
    amount: "Amount",
    pin_code: "PIN Code",
    organization: "Organization",
    language: "Language",
    keywords: "Keywords"
  };

  for (const [key, value] of Object.entries(data.extracted || {})) {
    const row = document.createElement("div");
    row.className = "field";

    const displayValue = Array.isArray(value)
      ? value.join(", ")
      : (value || "Not detected");

    row.innerHTML = `
      <div class="key">${labels[key] || key}</div>
      <div class="value"></div>
    `;

    row.querySelector(".value").textContent = displayValue;
    fields.appendChild(row);
  }

  document.getElementById("ocrText").textContent =
    data.ocr_text || "No OCR text detected.";

  document.getElementById("jsonBtn").onclick = () =>
    download(`/api/export/${data.id}/json`);

  document.getElementById("csvBtn").onclick = () =>
    download(`/api/export/${data.id}/csv`);

  document.getElementById("pdfBtn").onclick = () =>
    download(`/api/export/${data.id}/pdf`);
}

function languageName(code) {
  return {
    en: "English",
    hi: "Hindi",
    mr: "Marathi",
    kn: "Kannada"
  }[code] || code;
}

function download(url) {
  const link = document.createElement("a");
  link.href = url;
  link.click();
}

async function loadHistory() {
  const container = document.getElementById("history");

  try {
    const response = await fetch("/api/documents");
    const docs = await response.json();

    if (!docs.length) {
      container.innerHTML = "<p class='muted'>No processed documents yet.</p>";
      return;
    }

    container.innerHTML = docs.map(doc => `
      <div class="history-row">
        <div><strong>${escapeHtml(doc.filename)}</strong></div>
        <div>${languageName(doc.language)}</div>
        <div>${(doc.confidence * 100).toFixed(1)}%</div>
        <div>${new Date(doc.created_at).toLocaleString()}</div>
      </div>
    `).join("");
  } catch {
    container.innerHTML = "<p class='muted'>History unavailable.</p>";
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadHistory();
