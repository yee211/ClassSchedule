/**
 * 前端统一 API 客户端与凭据管理模块。
 */

const TOKEN_KEY = 'token';
const ACTIVE_SCHEDULE_KEY = 'active_schedule_id';
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getActiveScheduleId() {
  const id = localStorage.getItem(ACTIVE_SCHEDULE_KEY);
  return id ? Number(id) : null;
}

export function setActiveScheduleId(id) {
  if (id) {
    localStorage.setItem(ACTIVE_SCHEDULE_KEY, String(id));
  } else {
    localStorage.removeItem(ACTIVE_SCHEDULE_KEY);
  }
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ACTIVE_SCHEDULE_KEY);
}

export async function api(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(apiUrl(url), { ...options, headers });
  } catch (error) {
    if (error?.name === 'TimeoutError' || error?.name === 'AbortError') {
      throw new Error('请求超时，服务端可能仍在处理，请稍后刷新课表确认');
    }
    throw new Error('网络连接失败，请检查网络后重试');
  }
  let body = {};
  try {
    body = await response.json();
  } catch {
    // 允许空响应或非 JSON
  }

  if (!response.ok) {
    if (response.status === 401) {
      clearAuth();
      window.dispatchEvent(new CustomEvent('auth:expired'));
    }
    throw new Error(body.detail || '请求失败');
  }

  return response.status === 204 ? null : body;
}

export const authApi = {
  async register(data) {
    return api('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  async login(data) {
    return api('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  async me() {
    return api('/api/me');
  },
};

export const schedulesApi = {
  async list() {
    return api('/api/schedules');
  },
  async update(id, data) {
    return api(`/api/schedules/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  async delete(id) {
    return api(`/api/schedules/${id}`, { method: 'DELETE' });
  },
};

export const coursesApi = {
  async add(data) {
    return api('/api/courses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  async update(id, data) {
    return api(`/api/courses/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  async delete(id) {
    return api(`/api/courses/${id}`, { method: 'DELETE' });
  },
  async adjust(id, week, data) {
    return api(`/api/courses/${id}/adjustments/${week}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
  },
  async cancelAdjustment(id, week) {
    return api(`/api/courses/${id}/adjustments/${week}`, { method: 'DELETE' });
  },
};

export const adjustmentsApi = {
  async parse(file, scheduleId) {
    const form = new FormData();
    form.append('file', file);
    form.append('schedule_id', String(scheduleId));
    const signal = typeof AbortSignal !== 'undefined' && AbortSignal.timeout
      ? AbortSignal.timeout(30000)
      : undefined;
    return api('/api/adjustments/parse', { method: 'POST', body: form, signal });
  },
  async parseText(text, scheduleId) {
    const signal = typeof AbortSignal !== 'undefined' && AbortSignal.timeout
      ? AbortSignal.timeout(30000)
      : undefined;
    return api('/api/adjustments/parse-text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedule_id: scheduleId, text }),
      signal,
    });
  },
  async apply(scheduleId, items) {
    return api('/api/adjustments/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedule_id: scheduleId, items }),
    });
  },
};

export const importerApi = {
  async importFile(formData) {
    const signal = typeof AbortSignal !== 'undefined' && AbortSignal.timeout
      ? AbortSignal.timeout(75000)
      : undefined;
    return api('/api/import', {
      method: 'POST',
      body: formData,
      signal,
    });
  },
};

export const appApi = {
  async getVersion() {
    return api('/api/app/version');
  },
};
