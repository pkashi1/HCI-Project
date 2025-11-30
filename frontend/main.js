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

  // YouTube embed elements
  const youtubeEmbed = document.getElementById('youtubeEmbed');
  const youtubePlayer = document.getElementById('youtubePlayer');
  const toggleEmbedBtn = document.getElementById('toggleEmbed');

  // Small UI helpers
  function log(...args) {
    try {
      const line = document.createElement('div');
      line.textContent = args.map(a => (typeof a === 'string' ? a : JSON.stringify(a))).join(' ');
      logEl.prepend(line);
    } catch (e) {
      // ignore
      /* console.log(...args) */
    }
  }

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  function speak(text) {
    if (ttsMuted) return;
    if (!('speechSynthesis' in window)) {
      log('TTS not supported, assistant:', text);
      return;
    }
    try {
      const u = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch (e) {
      log('TTS error:', e.message || e);
    }
  }

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
  let ingestedVideoData = null; // store video metadata from ingestion

  // Speech recognition setup
  let recognition = null;
  let listening = false;
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;

  // Function to initialize speech recognition when needed
  function initializeSpeechRecognition() {
    if (!SpeechRecognition || recognition) return recognition;
    
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.continuous = true; // Enable continuous recognition

    recognition.addEventListener('result', (ev) => {
      const text = ev.results[ev.results.length - 1][0].transcript;
      log(`Heard: ${text}`);
      handleUserInput(text);
    });

    recognition.addEventListener('end', () => {
      // Only restart if we're still supposed to be listening
      // Add a small delay to prevent rapid restarts
      if (listening) {
        setTimeout(() => {
          if (listening) { // Check again after delay
            try {
              recognition.start();
            } catch (e) {
              console.log('Recognition restart failed:', e);
              listening = false;
              voiceToggle.textContent = '🎤 Start Listening';
            }
          }
        }, 100);
      }
    });

    recognition.addEventListener('error', (ev) => {
      log('ASR error: ' + ev.error);
      if (ev.error === 'not-allowed' || ev.error === 'permission-denied') {
        log('Microphone access denied');
      }
      listening = false;
      voiceToggle.textContent = '🎤 Start Listening';
    });

    return recognition;
  }
  startBtn.addEventListener('click', async (e) => {
    e.preventDefault();
  //  startBtn.addEventListener('click', async () => {
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
  ingestBtn.addEventListener('click', async (e) => {
    e.preventDefault();
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
      // Store video metadata for later use
      ingestedVideoData = {
        video_id: data.video_id,
        title: data.title,
        youtube_url: url
      };
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
  extractBtn.addEventListener('click', async (e) => {
    e.preventDefault();
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
      
      // Add video metadata to the extracted recipe if available
      console.log('Ingested video data:', ingestedVideoData);
      if (ingestedVideoData) {
        console.log('Adding video metadata to recipe');
        extractedRecipe.video_id = ingestedVideoData.video_id;
        extractedRecipe.video_title = ingestedVideoData.title;
        extractedRecipe.youtube_url = ingestedVideoData.youtube_url;
        console.log('Recipe after adding video metadata:', extractedRecipe);
      } else {
        console.log('No ingested video data available');
      }
      
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
    // Validate recipe object before sending to backend
    const valid = validateRecipe(recipe);
    if (!valid) {
      setStatus('Recipe validation failed — see log');
      return;
    }
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
      const newSessionId = data.session_id;
      setStatus('Session started (opened in new tab)');
      // Open started session in a new tab using same index page with session param
      const targetUrl = `index.html?session=${encodeURIComponent(newSessionId)}`;
      window.open(targetUrl, '_blank');
      // Keep current page on setup; do not reveal inline session UI
    } catch (e) {
      setStatus('Could not start session');
      log('Start exception:', e.message || e);
    }
  }

  // Auto-load session if index opened with ?session=<id>
  (async function autoLoadSessionFromParam() {
    const params = new URLSearchParams(window.location.search);
    const sid = params.get('session');
    if (!sid) return; // no session param; stay in setup mode
    setStatus('Loading session...');
    try {
      const resp = await fetch(`${BASE_URL}/session/${sid}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!resp.ok) {
        setStatus('Failed to load session');
        log('Load error:', await resp.text());
        return;
      }
      const data = await resp.json();
      //log('Session data:', data);
      console.log('Loaded session data:', data);
      console.log('Session data keys:', Object.keys(data));
      console.log('Session recipe data:', data.recipe);
      if (data.recipe) {
        console.log('Recipe keys:', Object.keys(data.recipe));
        console.log('Recipe video_id:', data.recipe.video_id);
      }
      
      sessionId = sid;
      totalSteps = data.total_steps || 0;
      currentStep = data.current_step || 0;
      recipeTitleEl.textContent = data.recipe_title || data.recipe?.title || 'Recipe';
      totalStepsEl.textContent = String(totalSteps);
      currentStepEl.textContent = String(currentStep);
      metaEl.textContent = `Session: ${sessionId}`;
      instructionEl.textContent = data.step_data?.instruction || 'No instruction loaded';
      
      // Setup YouTube embed if available
      setupYouTubeEmbed(data);
      
      document.getElementById('setup').classList.add('hidden');
      sessionSection.classList.remove('hidden');
      setStatus('Session loaded');
      if (instructionEl.textContent && !ttsMuted) speak(instructionEl.textContent);
    } catch (e) {
      setStatus('Could not load session');
      log('Load exception:', e.message || e);
    }
  })();

  // Client-side recipe validation
  function validateRecipe(recipe) {
    const errors = [];
    if (!recipe || typeof recipe !== 'object') {
      errors.push('Recipe must be a JSON object');
    } else {
      // Title check (optional)
      if (!recipe.title && !recipe.name) {
        errors.push('Recipe should include a title ("title" or "name")');
      }

      // Steps check
      if (!Array.isArray(recipe.steps)) {
        errors.push('Recipe must include a "steps" array');
      } else if (recipe.steps.length === 0) {
        errors.push('Recipe "steps" must not be empty');
      } else {
        recipe.steps.forEach((s, i) => {
          if (!s || typeof s !== 'object') {
            errors.push(`Step at index ${i} is not an object`);
            return;
          }
          if (!s.instruction || typeof s.instruction !== 'string' || s.instruction.trim() === '') {
            errors.push(`Step ${s.step_number || i+1} missing a non-empty "instruction" string`);
          }
          // optional: check step_number is numeric
          if (s.step_number != null && isNaN(Number(s.step_number))) {
            errors.push(`Step ${i+1} has invalid step_number`);
          }
        });
      }
    }

    if (errors.length) {
      log('Validation errors:');
      errors.forEach(e => log('• ' + e));
      return false;
    }
    return true;
  }


  clearBtn.addEventListener('click', () => {
    recipeFile.value = '';
    recipeText.value = '';
    youtubeUrl.value = '';
    ingestedVideoData = null; // Clear video metadata
    extractedRecipe = null; // Clear extracted recipe
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

      // Update UI if session state changed (current_step, total_steps are returned)
      if (data.current_step !== undefined) {
        currentStep = data.current_step;
        currentStepEl.textContent = String(currentStep);
      }
      if (data.total_steps !== undefined) {
        totalSteps = data.total_steps;
        totalStepsEl.textContent = String(totalSteps);
      }

      // Refresh current step instruction after navigation commands
      const lowerQuery = q.toLowerCase();
      if (lowerQuery.includes('next') || lowerQuery.includes('previous') || 
          lowerQuery.includes('repeat') || lowerQuery.includes('go to step')) {
        // Fetch current step data to update instruction
        try {
          const stepResp = await fetch(`${BASE_URL}/session/step`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, action: 'repeat' })
          });
          if (stepResp.ok) {
            const stepData = await stepResp.json();
            if (stepData.step_data?.instruction) {
              instructionEl.textContent = stepData.step_data.instruction;
            }
          }
        } catch (e) {
          // Silent fail - don't break the main query flow
        }
      }
    } catch (e) {
      log('Query exception: ' + e.message);
    }
  }

  // Voice controls
  voiceToggle.addEventListener('click', () => {
    if (!SpeechRecognition) {
      alert('SpeechRecognition not supported in this browser. Use Chrome/Edge with microphone.');
      return;
    }

    // Initialize speech recognition on first click (this triggers permission prompt)
    if (!recognition) {
      recognition = initializeSpeechRecognition();
      if (!recognition) {
        alert('Failed to initialize speech recognition.');
        return;
      }
    }

    listening = !listening;
    if (listening) {
      recognition.start(); // This will prompt for microphone access on first use
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

  // YouTube embed toggle
  toggleEmbedBtn.addEventListener('click', () => {
    const isMinimized = youtubeEmbed.classList.contains('minimized');
    if (isMinimized) {
      youtubeEmbed.classList.remove('minimized');
      toggleEmbedBtn.textContent = 'Hide Video';
    } else {
      youtubeEmbed.classList.add('minimized');
      toggleEmbedBtn.textContent = 'Show Video';
    }
  });

  // Test function to manually check a video ID (for debugging)
  window.testYouTubeEmbed = function(videoId) {
    console.log('Testing video ID:', videoId);
    setupYouTubeEmbed({video_id: videoId});
  };

  // Setup YouTube embed if video ID is available
  function setupYouTubeEmbed(recipeData) {
    console.log('Setting up YouTube embed with data:', recipeData);
    console.log('Recipe data keys:', Object.keys(recipeData || {}));
    console.log('Recipe nested data:', recipeData?.recipe ? Object.keys(recipeData.recipe) : 'no recipe property');
    
    // Look for video_id in multiple possible locations
    const videoId = recipeData?.video_id || 
                   recipeData?.recipe?.video_id || 
                   recipeData?.recipe?.video?.id ||
                   recipeData?.videoId;
                   
    console.log('Checking video_id locations:');
    console.log('- recipeData.video_id:', recipeData?.video_id);
    console.log('- recipeData.recipe.video_id:', recipeData?.recipe?.video_id);
    console.log('- recipeData.recipe.video.id:', recipeData?.recipe?.video?.id);
    console.log('- recipeData.videoId:', recipeData?.videoId);
    console.log('Final video_id:', videoId);
    
    if (videoId) {
      // Validate video ID format (should be 11 characters)
      if (!/^[a-zA-Z0-9_-]{11}$/.test(videoId)) {
        console.error('Invalid YouTube video ID format:', videoId);
        log(`❌ Invalid video ID format: ${videoId}`);
        youtubeEmbed.classList.add('hidden');
        return;
      }
      
      // Try YouTube's privacy-enhanced mode first
      const embedUrl = `https://www.youtube-nocookie.com/embed/${videoId}`;
      console.log('Setting embed URL (privacy-enhanced):', embedUrl);
      
      // Test if the video exists by trying to load it
      console.log('Testing video availability at:', `https://www.youtube.com/watch?v=${videoId}`);
      
      // Create fallback content for embedding failures
      const videoContainer = youtubeEmbed.querySelector('.video-container');
      const watchUrl = `https://www.youtube.com/watch?v=${videoId}`;
      
      // Remove any existing fallback
      const existingFallback = videoContainer.querySelector('.video-fallback');
      if (existingFallback) {
        existingFallback.remove();
      }
      
      // Create fallback div
      const fallbackDiv = document.createElement('div');
      fallbackDiv.className = 'video-fallback';
      fallbackDiv.style.cssText = `
        display: none;
        padding: 40px 20px;
        text-align: center;
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-radius: 8px;
        border: 2px dashed #cbd5e0;
      `;
      
      fallbackDiv.innerHTML = `
        <div style="margin-bottom: 16px; font-size: 24px;">🎥</div>
        <div style="margin-bottom: 12px; font-weight: 600; color: #2d3748; font-size: 18px;">Recipe Video Available</div>
        <div style="margin-bottom: 16px; color: #4a5568; font-size: 14px;">This video cannot be embedded due to YouTube restrictions</div>
        <a href="${watchUrl}" target="_blank" style="
          display: inline-block;
          background: #ff0000;
          color: white;
          padding: 12px 24px;
          border-radius: 6px;
          text-decoration: none;
          font-weight: 600;
          font-size: 16px;
          transition: all 0.2s;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        " onmouseover="this.style.background='#cc0000'; this.style.transform='translateY(-1px)'" onmouseout="this.style.background='#ff0000'; this.style.transform='translateY(0)'">
          ▶ Watch on YouTube
        </a>
      `;
      
      videoContainer.appendChild(fallbackDiv);
      
      // Try to embed the video first
      youtubePlayer.src = embedUrl;
      youtubeEmbed.classList.remove('hidden');
      log(`� Attempting to embed video: ${videoId}`);
      
      // Show fallback if embedding fails (Error 153 appears quickly)
      setTimeout(() => {
        // For Error 153, show the fallback immediately
        fallbackDiv.style.display = 'block';
        youtubePlayer.style.display = 'none';
        log(`🔗 Showing YouTube link instead of embed for: ${videoId}`);
      }, 2000);
    } else {
      console.log('No video_id found, hiding embed');
      youtubeEmbed.classList.add('hidden');
    }
  }

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
