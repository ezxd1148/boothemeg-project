import { API_BASE_URL, API_TIMEOUT, ENDPOINTS } from "@/constants/api";

// ── Types ───────────────────────────────────────────────────────────────────
export interface Notification {
  app: string;
  sender: string | null;
  message: string;
  time: string | null;
  category: string | null;
}

export interface CalendarEvent {
  title: string | null;
  date: string | null;
  time: string | null;
  duration_minutes: number | null;
  sender: string | null;
  description: string | null;
  location: string | null;
  attendees: string[];
  recurrence: string | null;
  is_schedulable: boolean;
  _source?: string;
}

export interface CalendarAddResult {
  added: number;
  skipped: number;
  events: Array<{
    summary?: string;
    start?: string;
    link?: string;
    error?: string;
  }>;
}

export interface PipelineResult {
  processed: number;
  schedulable: number;
  added: number;
  skipped: number;
  events: CalendarAddResult["events"];
}

export interface HealthResponse {
  status: string;
  cors: boolean;
  rate_limiting: boolean;
  endpoints: string[];
}

export interface ApiError {
  error: string;
}

// ── Helpers ─────────────────────────────────────────────────────────────────
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(
        (body as ApiError).error ||
          `HTTP ${response.status}: ${response.statusText}`,
      );
    }

    return (await response.json()) as T;
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new Error("Request timed out. Is the server running?");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ── API methods ─────────────────────────────────────────────────────────────

/** Check if the backend is reachable */
export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>(ENDPOINTS.health);
}

/** Send raw notifications to the AI processor, get calendar events back */
export async function processNotifications(
  notifications: Notification[],
): Promise<CalendarEvent[]> {
  return request<CalendarEvent[]>(ENDPOINTS.processNotifications, {
    method: "POST",
    body: JSON.stringify(notifications),
  });
}

/** Add calendar events to Google Calendar */
export async function addToCalendar(
  events: CalendarEvent[],
): Promise<CalendarAddResult> {
  return request<CalendarAddResult>(ENDPOINTS.calendarAdd, {
    method: "POST",
    body: JSON.stringify(events),
  });
}

/** Run the full pipeline: notifications → AI → Google Calendar */
export async function runPipeline(
  notifications: Notification[],
): Promise<PipelineResult> {
  return request<PipelineResult>(ENDPOINTS.pipelineRun, {
    method: "POST",
    body: JSON.stringify(notifications),
  });
}
