const askForm = document.getElementById("ask-form");
const questionInput = document.getElementById("question-input");
const micBtn = document.getElementById("mic-btn");
const speakToggle = document.getElementById("speak-toggle");
const statusEl = document.getElementById("status");
const ingestBtn = document.getElementById("ingest-btn");
const ingestStatus = document.getElementById("ingest-status");

const answerSection = document.getElementById("answer-section");
const answerQuestion = document.getElementById("answer-question");
const answerText = document.getElementById("answer-text");
const answerAudio = document.getElementById("answer-audio");
const sourcesSection = document.getElementById("sources-section");
const sourcesList = document.getElementById("sources-list");

function setStatus(msg) {
  statusEl.textContent = msg;
}

function renderAnswer({ question, answer, sources, audio_base64 }) {
  answerQuestion.textContent = question ? `you asked: "${question}"` : "";
  answerQuestion.hidden = !question;
  answerText.textContent = answer;
  answerSection.hidden = false;

  sourcesList.innerHTML = "";
  if (sources && sources.length) {
    sources.forEach((s) => {
      const li = document.createElement("li");
      const score = document.createElement("span");
      score.className = "score";
      score.textContent = s.score.toFixed(3);
      const title = document.createElement("strong");
      title.textContent = s.title;
      const text = document.createElement("p");
      text.textContent = s.text;
      li.append(score, title, text);
      sourcesList.appendChild(li);
    });
    sourcesSection.hidden = false;
  } else {
    sourcesSection.hidden = true;
  }

  if (audio_base64) {
    answerAudio.src = `data:audio/mpeg;base64,${audio_base64}`;
    answerAudio.hidden = false;
    answerAudio.play().catch(() => {});
  } else {
    answerAudio.hidden = true;
    answerAudio.removeAttribute("src");
  }
}

ingestBtn.addEventListener("click", async () => {
  ingestStatus.textContent = " indexing...";
  ingestBtn.disabled = true;
  try {
    const res = await fetch("/api/ingest", { method: "POST" });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    ingestStatus.textContent = ` done — ${data.embedded_ready}/${data.documents_uploaded} documents ready.`;
  } catch (err) {
    ingestStatus.textContent = " failed — see console.";
    console.error(err);
  } finally {
    ingestBtn.disabled = false;
  }
});

askForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;
  setStatus("thinking...");
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, speak: speakToggle.checked }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderAnswer({ question, answer: data.answer, sources: data.sources, audio_base64: data.audio_base64 });
    setStatus("");
  } catch (err) {
    setStatus("Something went wrong — see console.");
    console.error(err);
  }
});

// --- Voice input: record with MediaRecorder, POST the blob, play back the spoken reply ---
let mediaRecorder = null;
let chunks = [];
let recording = false;

micBtn.addEventListener("click", async () => {
  if (!recording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunks, { type: "audio/webm" });
        await sendVoiceQuestion(blob);
      };
      mediaRecorder.start();
      recording = true;
      micBtn.classList.add("recording");
      micBtn.textContent = "⏹";
      setStatus("listening... click 🎤 again to stop");
    } catch (err) {
      setStatus("Microphone access denied or unavailable.");
      console.error(err);
    }
  } else {
    mediaRecorder.stop();
    recording = false;
    micBtn.classList.remove("recording");
    micBtn.textContent = "🎤";
  }
});

async function sendVoiceQuestion(blob) {
  setStatus("transcribing + thinking...");
  const form = new FormData();
  form.append("audio", blob, "recording.webm");
  try {
    const res = await fetch("/api/ask-voice", { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderAnswer(data);
    setStatus("");
  } catch (err) {
    setStatus("Something went wrong — see console.");
    console.error(err);
  }
}
