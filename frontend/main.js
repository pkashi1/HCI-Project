// Frontend integration with backend voice session endpoints
// - POST /session/start  { recipe }
// - POST /session/step   { session_id, action }
// - POST /session/query  { session_id, query }

const BASE_URL = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'http://localhost:8000'; // adjust if backend runs elsewhere

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const recipeFile = document.getElementById('recipeFile');
  const recipeText = document.getElementById('recipeText');
  const youtubeUrl = document.getElementById('youtubeUrl');
  const ingestBtn = document.getElementById('ingestBtn');
  const extractBtn = document.getElementById('extractBtn');
  const startBtn = document.getElementById('startBtn');
  const clearBtn = document.getElementById('clearBtn');
  const statusEl = document.getElementById('status');

  const sessionSection = document.getElementById('session');
  const recipeTitleEl = document.getElementById('recipeTitle');
  const metaEl = document.getElementById('meta');
  const currentStepEl = document.getElementById('currentStep');
  const totalStepsEl = document.getElementById('totalSteps');
  const instructionEl = document.getElementById('instruction');
  const logEl = document.getElementById('log');
  const backendUrlEl = document.getElementById('backendUrl');
  backendUrlEl.textContent = BASE_URL;

  const nextBtn = document.getElementById('nextBtn');
  const prevBtn = document.getElementById('prevBtn');
  const repeatBtn = document.getElementById('repeatBtn');
  const askInput = document.getElementById('askInput');
  const askBtn = document.getElementById('askBtn');
  const voiceToggle = document.getElementById('voiceToggle');
  const muteTts = document.getElementById('muteTts');

  let sessionId = null;
  let totalSteps = 0;
  let currentStep = 0;
  let ttsMuted = false;
  let extractedRecipe = null; // store recipe produced by /extract

  // Speech recognition setup
  let recognition = null;
  let listening = false;
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.addEventListener('result', (ev) => {
      const text = ev.results[0][0].transcript;
      log(`Heard: ${text}`);
      handleUserInput(text);
    });

    recognition.addEventListener('end', () => {
      if (listening) recognition.start();
    });

    recognition.addEventListener('error', (ev) => {
      log('ASR error: ' + ev.error);
      listening = false;
      voiceToggle.textContent = '🎤 Start Listening';
    });
  }
  startBtn.addEventListener('click', async () => {
    // If we already have an extracted recipe, use it
    if (extractedRecipe) {
      await startSessionWithRecipe(extractedRecipe);
      return;
    }

    let content = '';
    if (recipeFile.files && recipeFile.files[0]) {
      try {
        content = await readFile(recipeFile.files[0]);
      } catch (e) {
        setStatus('Failed to read file');
        return;
      }
    } else if (recipeText.value.trim()) {
      content = recipeText.value.trim();
    } else {
      setStatus('Provide a recipe JSON (file or paste) or extract from YouTube');
      return;
    }

    let recipe = null;
    try {
      recipe = JSON.parse(content);
    } catch (e) {
      setStatus('Invalid JSON');
      return;
    }

    await startSessionWithRecipe(recipe);
  });

  // Ingest from YouTube: call /ingest and populate transcript area
  ingestBtn.addEventListener('click', async () => {
    const url = youtubeUrl.value.trim();
    if (!url) {
      setStatus('Enter a YouTube URL');
      return;
    }
    setStatus('Ingesting...');
    try {
      const resp = await fetch(`${BASE_URL}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ youtube_url: url })
      });
      if (!resp.ok) {
        const txt = await resp.text();
        setStatus('Ingest failed: ' + resp.status);
        log('Ingest error:', txt);
        return;
      }
      const data = await resp.json();
      // Put transcript into textarea for inspection or edit
      recipeText.value = data.transcript || '';
      // Remember title in UI
      recipeTitleEl.textContent = data.title || 'Ingested Video';
      setStatus('Ingest complete — transcript loaded');
      log(`Ingested: ${data.title} (${data.video_id})`);
    } catch (e) {
      setStatus('Ingest exception');
      log('Ingest exception:', e.message || e);
    }
  });

  // Extract recipe from transcript: call /extract and start session
  extractBtn.addEventListener('click', async () => {
    const transcript = recipeText.value.trim();
    if (!transcript) {
      setStatus('No transcript available to extract from');
      return;
    }
    setStatus('Extracting recipe...');
    try {
      const resp = await fetch(`${BASE_URL}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript })
      });
      if (!resp.ok) {
        const txt = await resp.text();
        setStatus('Extract failed: ' + resp.status);
        log('Extract error:', txt);
        return;
      }
      const data = await resp.json();
      extractedRecipe = data.recipe;
      setStatus('Recipe extracted — starting session');
      log('Extracted recipe:', extractedRecipe.title || extractedRecipe.name || 'recipe');
      await startSessionWithRecipe(extractedRecipe);
    } catch (e) {
      setStatus('Extract exception');
      log('Extract exception:', e.message || e);
    }
  });

  // Helper: start session given a recipe object
  async function startSessionWithRecipe(recipe) {
    setStatus('Starting session...');
    try {
      const resp = await fetch(`${BASE_URL}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipe })
      });
      if (!resp.ok) {
        const txt = await resp.text();
        setStatus('Start failed: ' + resp.status);
        log('Start error:', txt);
        return;
      }
      const data = await resp.json();
      sessionId = data.session_id;
      totalSteps = data.total_steps || 0;
      recipeTitleEl.textContent = data.recipe_title || (recipe.title || 'Recipe');
      totalStepsEl.textContent = String(totalSteps);
      metaEl.textContent = `Session: ${sessionId}`;
      setStatus('Session started');
      document.getElementById('setup').classList.add('hidden');
      sessionSection.classList.remove('hidden');

      await navigate('repeat', { speakOnLoad: true });
    } catch (e) {
      setStatus('Could not start session');
      log('Start exception:', e.message || e);
    }
  }


  clearBtn.addEventListener('click', () => {
    recipeFile.value = '';
    recipeText.value = '';
    setStatus('Idle');
  });

  // Navigation
  nextBtn.addEventListener('click', () => navigate('next', { speakOnLoad: true }));
  prevBtn.addEventListener('click', () => navigate('previous', { speakOnLoad: true }));
  repeatBtn.addEventListener('click', () => navigate('repeat', { speakOnLoad: true }));

  async function navigate(action, opts = {}) {
    if (!sessionId) return;
    try {
      const resp = await fetch(`${BASE_URL}/session/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, action })
      });
      if (!resp.ok) {
        log('Step error: ' + resp.status);
        return;
      }
      const data = await resp.json();
      const stepData = data.step_data;
      currentStep = data.current_step || currentStep;
      currentStepEl.textContent = String(currentStep);
      totalStepsEl.textContent = String(data.total_steps || totalSteps || '-');
      if (stepData && stepData.instruction) {
        instructionEl.textContent = stepData.instruction;
        if (opts.speakOnLoad !== false) speak(stepData.instruction);
      } else {
        instructionEl.textContent = 'No instruction returned';
      }
    } catch (e) {
      log('Navigate exception: ' + e.message);
    }
  }

  // Ask / query
  askBtn.addEventListener('click', () => {
    const q = askInput.value.trim();
    if (!q) return;
    askInput.value = '';
    query(q);
  });

  askInput.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter') {
      askBtn.click();
    }
  });

  async function query(q) {
    if (!sessionId) return;
    log('You: ' + q);
    try {
      const resp = await fetch(`${BASE_URL}/session/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, query: q })
      });
      if (!resp.ok) {
        log('Query error: ' + resp.status);
        return;
      }
      const data = await resp.json();
      const responseText = data.response || JSON.stringify(data);
      log('Assistant: ' + responseText);
      speak(responseText);
    } catch (e) {
      log('Query exception: ' + e.message);
    }
  }

  // Voice controls
  voiceToggle.addEventListener('click', () => {
    if (!recognition) {
      alert('SpeechRecognition not supported in this browser. Use Chrome/Edge with microphone.');
      return;
    }
    listening = !listening;
    if (listening) {
      recognition.start();
      voiceToggle.textContent = '🎤 Listening... (click to stop)';
      log('Listening started');
    } else {
      recognition.stop();
      voiceToggle.textContent = '🎤 Start Listening';
      log('Listening stopped');
    }
  });

  muteTts.addEventListener('click', () => {
    ttsMuted = !ttsMuted;
    muteTts.textContent = ttsMuted ? '🔈 Unmute TTS' : '🔇 Mute TTS';
  });

  // Handle textual commands from ASR or typed
  function handleUserInput(text) {
    const user = text.trim();
    if (!user) return;
    const lower = user.toLowerCase();

    // Control keywords
    if (lower.includes('next')) {
      navigate('next', { speakOnLoad: true });
      return;
    }
    if (lower.includes('previous') || lower.includes('back')) {
      navigate('previous', { speakOnLoad: true });
      return;
    }
    if (lower.includes('repeat') || lower.includes('again')) {
      navigate('repeat', { speakOnLoad: true });
      return;
    }
    if (['quit','stop','exit','goodbye'].some(w => lower.includes(w))) {
      speak('Happy cooking! Goodbye!');
      // reload UI to allow new session
      window.location.reload();
      return;
    }

    // Otherwise send as a query
    query(user);
  }

  // Utility: read File -> text
  function readFile(file) {
    return new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(r.result);
      r.onerror = () => reject(r.error);
      r.readAsText(file);
    });
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', (ev) => {
    if (ev.key === 'ArrowRight') nextBtn.click();
    if (ev.key === 'ArrowLeft') prevBtn.click();
    if (ev.key === 'r') repeatBtn.click();
    if (ev.key === 'l') voiceToggle.click();
  });

});
