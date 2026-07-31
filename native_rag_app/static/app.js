// Build order: 08/09.
//
// app.js -- frontend for the MeshAPI-native RAG demo.
//
// Handles three things against the JSON API:
//   1. Indexing the knowledge base (POST /api/ingest)
//   2. Asking a typed question    (POST /api/ask)
//   3. Asking by voice            (records mic audio, POST /api/ask-voice)
// It then renders the answer, its sources, and optionally plays back spoken audio.

// --- Cache references to the DOM elements we interact with ---
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

// Small helper to update the single status line under the form.
function setStatus(msg) {
  statusEl.textContent = msg;
}

// FastAPI errors arrive as JSON like {"detail": "..."}; pull out a readable
// message, falling back to the raw error text.
function errorMessage(err) {
  try {
    return JSON.parse(err.message).detail || err.message;
  } catch {
    return err.message || "Something went wrong.";
  }
}

// Render an answer payload: the question echo, the answer text, source chunks,
// and (if present) the spoken audio.
function renderAnswer({ question, answer, sources, audio_base64 }) {
  // Echo back what was asked (used mainly for voice, where the user spoke it).
  answerQuestion.textContent = question ? `you asked: "${question}"` : "";
  answerQuestion.hidden = !question;
  answerText.textContent = answer;
  answerSection.hidden = false;

  // Rebuild the sources list from scratch each time.
  sourcesList.innerHTML = "";
  if (sources && sources.length) {
    sources.forEach((s) => {
      const li = document.createElement("li");
      const score = document.createElement("span");
      score.className = "score";
      score.textContent = s.score.toFixed(3);   // similarity score
      const title = document.createElement("strong");
      title.textContent = s.title;              // source document title
      const text = document.createElement("p");
      text.textContent = s.text;                // the retrieved chunk
      li.append(score, title, text);
      sourcesList.appendChild(li);
    });
    sourcesSection.hidden = false;
  } else {
    sourcesSection.hidden = true;
  }

  // If the server returned spoken audio, load it and auto-play (ignore autoplay
  // rejections, which some browsers enforce without a user gesture).
  if (audio_base64) {
    answerAudio.src = `data:audio/mpeg;base64,${audio_base64}`;
    answerAudio.hidden = false;
    answerAudio.play().catch(() => {});
  } else {
    answerAudio.hidden = true;
    answerAudio.removeAttribute("src");
  }
}

// --- Index the sample knowledge base (upload + embed) ---
ingestBtn.addEventListener("click", async () => {
  ingestStatus.textContent = " indexing...";
  ingestBtn.disabled = true;   // prevent double-submits while it runs
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

// --- Ask a typed question ---
askForm.addEventListener("submit", async (e) => {
  e.preventDefault();   // keep the page from reloading on submit
  const question = questionInput.value.trim();
  if (!question) return;
  setStatus("thinking...");
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // `speak` mirrors the checkbox: ask for spoken audio back or not.
      body: JSON.stringify({ question, speak: speakToggle.checked }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderAnswer({ question, answer: data.answer, sources: data.sources, audio_base64: data.audio_base64 });
    setStatus("");
  } catch (err) {
    setStatus(errorMessage(err));
    console.error(err);
  }
});

// --- Voice input: record with MediaRecorder, POST the blob, play back the spoken reply ---
let mediaRecorder = null;   // active MediaRecorder while recording
let chunks = [];            // collected audio data chunks
let recording = false;      // toggles between start/stop on each mic click

micBtn.addEventListener("click", async () => {
  if (!recording) {
    // --- Start recording ---
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks = [];
      mediaRecorder = new MediaRecorder(stream);
      // Gather audio as it becomes available.
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      // When stopped, release the mic and send the recorded blob.
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());   // free the microphone
        const blob = new Blob(chunks, { type: "audio/webm" });
        await sendVoiceQuestion(blob);
      };
      mediaRecorder.start();
      recording = true;
      micBtn.classList.add("recording");
      micBtn.textContent = "⏹";   // stop icon
      setStatus("listening... click 🎤 again to stop");
    } catch (err) {
      setStatus("Microphone access denied or unavailable.");
      console.error(err);
    }
  } else {
    // --- Stop recording (triggers onstop above) ---
    mediaRecorder.stop();
    recording = false;
    micBtn.classList.remove("recording");
    micBtn.textContent = "🎤";   // mic icon
  }
}); 

// Upload the recorded audio to the voice endpoint and render the spoken answer.
async function sendVoiceQuestion(blob) {
  setStatus("transcribing + thinking...");
  const form = new FormData();
  form.append("audio", blob, "recording.webm");   // multipart field name must match FastAPI's `audio`
  try {
    const res = await fetch("/api/ask-voice", { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    renderAnswer(data);   // includes the transcribed question + audio
    setStatus("");
  } catch (err) {
    setStatus(errorMessage(err));
    console.error(err);
  }
}
