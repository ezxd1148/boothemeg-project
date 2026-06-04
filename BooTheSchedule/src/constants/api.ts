/**
 * API configuration for the Flask backend.
 * Change BASE_URL to point to your running Flask server.
 * For Expo Go on physical device, use your machine's LAN IP.
 */

// Auto-detect: use localhost for web/simulator, LAN IP for physical device
// Override this with your actual server IP when testing on a real phone
export const API_BASE_URL = __DEV__
  ? "http://192.168.0.62:5000" // ← CHANGE THIS to your machine's LAN IP
  : "https://your-production-server.com";

export const ENDPOINTS = {
  health: "/",
  processNotifications: "/notifications/process",
  calendarAdd: "/calendar/add",
  pipelineRun: "/pipeline/run",
} as const;

// Request timeout in milliseconds
export const API_TIMEOUT = 30_000;
