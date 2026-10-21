/**
 * Unified API Client for AI Knowledge Assistant
 * Connects to FastAPI backend via Vite proxy or custom base URL.
 */

const API_BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

function getStoredToken() {
  return localStorage.getItem('access_token');
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem('access_token', token);
  } else {
    localStorage.removeItem('access_token');
  }
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getStoredToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  // Handle HTML response (e.g. GET /auth/verify-email)
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('text/html')) {
    const text = await response.text();
    if (!response.ok) {
      throw new ApiError('Verification failed', response.status, text);
    }
    return { html: text };
  }

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    let errorMessage = `HTTP error ${response.status}`;
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        errorMessage = data.detail;
      } else if (Array.isArray(data.detail)) {
        // FastAPI validation errors
        errorMessage = data.detail
          .map((item) => `${item.loc ? item.loc.join('.') + ': ' : ''}${item.msg}`)
          .join(', ');
      }
    } else if (data?.message) {
      errorMessage = data.message;
    }

    throw new ApiError(errorMessage, response.status, data);
  }

  return data;
}

export const api = {
  // Authentication
  auth: {
    register: (payload) =>
      request('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    verifyEmail: (token) =>
      request(`/auth/verify-email?token=${encodeURIComponent(token)}`, {
        method: 'GET',
      }),
    resendVerification: (email) =>
      request('/auth/resend-verification', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
    login: (credentials) =>
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),
    getMe: () => request('/auth/me', { method: 'GET' }),
  },

  // Conversations & Chat
  conversations: {
    list: () => request('/conversations', { method: 'GET' }),
    create: () => request('/conversations', { method: 'POST' }),
    getMessages: (conversationId) =>
      request(`/conversations/${conversationId}/messages`, { method: 'GET' }),
    sendMessage: (conversationId, message) =>
      request(`/conversations/${conversationId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ message }),
      }),
    extractMemories: (conversationId) =>
      request(`/conversations/${conversationId}/extract-memories`, {
        method: 'POST',
      }),
    createEpisode: (conversationId) =>
      request(`/conversations/${conversationId}/episode`, {
        method: 'POST',
      }),
  },

  // Episodic Memory
  episodes: {
    list: () => request('/episodes', { method: 'GET' }),
  },

  // Long-Term Memory
  memories: {
    list: () => request('/memories', { method: 'GET' }),
    create: (data) =>
      request('/memories', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (memoryId, data) =>
      request(`/memories/${memoryId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    delete: (memoryId) =>
      request(`/memories/${memoryId}`, {
        method: 'DELETE',
      }),
  },
};
