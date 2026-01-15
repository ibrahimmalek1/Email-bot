/**
 * API service for Email Summarizer backend
 */
const API_BASE = 'http://localhost:8000';

// Auth endpoints
export const checkAuthStatus = async () => {
  const res = await fetch(`${API_BASE}/auth/status`);
  return res.json();
};

export const getLoginUrl = () => `${API_BASE}/auth/login`;

export const logout = async () => {
  const res = await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
  return res.json();
};

// Settings endpoints
export const checkGeminiStatus = async () => {
  const res = await fetch(`${API_BASE}/settings/gemini/status`);
  return res.json();
};

export const saveGeminiKey = async (apiKey) => {
  const res = await fetch(`${API_BASE}/settings/gemini`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ api_key: apiKey })
  });
  return res.json();
};

export const saveGoogleAuth = async (clientId, clientSecret) => {
  const res = await fetch(`${API_BASE}/auth/setup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret })
  });
  return res.json();
};

// Email endpoints
export const fetchEmails = async (params = {}) => {
  const res = await fetch(`${API_BASE}/emails/fetch/gmail`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  return res.json();
};

export const getEmailSummaries = async (filters = {}) => {
  const queryParams = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      queryParams.append(key, value);
    }
  });

  // Add timestamp for cache busting
  queryParams.append('_t', new Date().getTime());

  const url = `${API_BASE}/emails/summaries?${queryParams.toString()}`;
  const res = await fetch(url);
  return res.json();
};

export const getEmailStats = async () => {
  const res = await fetch(`${API_BASE}/emails/summaries/stats`);
  return res.json();
};

export const deleteAllSummaries = async () => {
  const res = await fetch(`${API_BASE}/emails/summaries`, { method: 'DELETE' });
  return res.json();
};

export const generateSummaryReport = async (filters = {}) => {
  const res = await fetch(`${API_BASE}/reports/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(filters),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.report || "Failed to generate summary");
  }
  return res.json();
};

