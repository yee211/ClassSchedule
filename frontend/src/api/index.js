/**
 * 前端统一 API 客户端与凭据管理模块。
 */

const TOKEN_KEY = 'token';
const ACTIVE_SCHEDULE_KEY = 'active_schedule_id';

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

  const response = await fetch(url, { ...options, headers });
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
};

export const importerApi = {
  async importFile(formData) {
    return api('/api/import', {
      method: 'POST',
      body: formData,
    });
  },
};
