export async function apiFetch(url: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  const token = localStorage.getItem('evaluator_token');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && typeof options.body === 'string' && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const response = await fetch(url, { ...options, headers });
  if (response.status === 401) window.dispatchEvent(new Event('session-expired'));
  return response;
}

export async function apiJson(url: string, options: RequestInit = {}) {
  const response = await apiFetch(url, options);
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(item => item.msg).join('; ') : `Request failed (${response.status})`);
  }
  return data;
}
