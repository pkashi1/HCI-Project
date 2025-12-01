// API service for communicating with the backend
const BASE_URL = 'http://localhost:8000';

export interface SavedRecipe {
  id: number;
  title: string;
  description: string;
  recipe: Recipe;
  created_at: number;
  updated_at: number;
}

export interface Recipe {
  title: string;
  description?: string;
  image?: string;
  ingredients: Record<string, string[]>;
  kitchen_tools_and_dishes: string[];
  steps: Array<{
    step_number: number;
    instruction: string;
    estimated_time?: string;
  }>;
  servings?: string;
  total_time?: string;
  video_url?: string;
  [key: string]: any;
}

export interface IngestRequest {
  youtube_url: string;
}

export interface IngestResponse {
  video_id: string;
  title: string;
  transcript: string;
  snippet_count: number;
  thumbnail?: string;
  url?: string;
}

export interface ExtractRequest {
  transcript: string;
  model?: string;
}

export interface ExtractResponse {
  recipe: Recipe;
}

export interface SessionStartRequest {
  recipe: Recipe;
}

export interface SessionStartResponse {
  session_id: string;
  recipe_title: string;
  total_steps: number;
}

export interface SessionQueryRequest {
  session_id: string;
  query: string;
  image?: string;
}

export interface SessionQueryResponse {
  response: string;
  current_step: number;
  total_steps: number;
  active_timers: Array<{
    id: string;
    label: string;
    seconds_total: number;
    seconds_remaining: number;
    status: string;
    started_at: number;
  }>;
  is_paused: boolean;
}

export interface TimerRequest {
  session_id: string;
  label: string;
  duration: string;
}

export interface TimerResponse {
  timer_id: string;
  label: string;
  seconds_total: number;
  seconds_remaining: number;
}

export interface StepNavigationRequest {
  session_id: string;
  action: string;
}

export interface SessionState {
  session_id: string;
  recipe: Recipe;
  current_step: number;
  total_steps: number;
  current_step_data: {
    step_number: number;
    instruction: string;
    estimated_time?: string;
  } | null;
  timers: Array<{
    id: string;
    label: string;
    seconds_total: number;
    seconds_remaining: number;
    status: string;
    started_at: number;
  }>;
  active_timers: Array<{
    id: string;
    label: string;
    seconds_total: number;
    seconds_remaining: number;
    status: string;
    started_at: number;
  }>;
  created_at: number;
  notes: string[];
  is_paused: boolean;
}

// API functions
export async function ingestVideo(request: IngestRequest): Promise<IngestResponse> {
  const response = await fetch(`${BASE_URL}/ingest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to ingest video: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function extractRecipe(request: ExtractRequest): Promise<ExtractResponse> {
  const response = await fetch(`${BASE_URL}/extract`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to extract recipe: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function startSession(request: SessionStartRequest): Promise<SessionStartResponse> {
  const response = await fetch(`${BASE_URL}/session/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to start session: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function querySession(request: SessionQueryRequest): Promise<SessionQueryResponse> {
  const response = await fetch(`${BASE_URL}/session/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to query session: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function navigateStep(request: StepNavigationRequest): Promise<any> {
  const response = await fetch(`${BASE_URL}/session/step`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to navigate step: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function addTimer(request: TimerRequest): Promise<TimerResponse> {
  const response = await fetch(`${BASE_URL}/session/timer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Failed to add timer: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function getSessionState(sessionId: string): Promise<SessionState> {
  const response = await fetch(`${BASE_URL}/session/${encodeURIComponent(sessionId)}`);

  if (!response.ok) {
    throw new Error(`Failed to get session state: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function listSessions(): Promise<{ sessions: string[]; count: number }> {
  const response = await fetch(`${BASE_URL}/sessions`);

  if (!response.ok) {
    throw new Error(`Failed to list sessions: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

// Recipe management functions
export async function saveRecipe(title: string, description: string, recipe: Recipe): Promise<SavedRecipe> {
  const response = await fetch(`${BASE_URL}/recipes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title, description, recipe }),
  });

  if (!response.ok) {
    throw new Error(`Failed to save recipe: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function listRecipes(): Promise<SavedRecipe[]> {
  const response = await fetch(`${BASE_URL}/recipes`);

  if (!response.ok) {
    throw new Error(`Failed to list recipes: ${response.status} ${await response.text()}`);
  }

  return response.json();
}

export async function getRecipe(id: number): Promise<SavedRecipe> {
  const response = await fetch(`${BASE_URL}/recipes/${id}`);

  if (!response.ok) {
    throw new Error(`Failed to get recipe: ${response.status} ${await response.text()}`);
  }

  return response.json();
}