const DEFAULT_API_BASE = 'http://127.0.0.1:8001';

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE).replace(/\/$/, '');
}

export async function healthCheck() {
  const [backendResponse, modelResponse] = await Promise.all([
    fetch(`${getApiBaseUrl()}/health`),
    fetch(`${getApiBaseUrl()}/api/model/health`)
  ]);

  if (!backendResponse.ok) {
    throw new Error(`Backend health check failed (${backendResponse.status}).`);
  }

  const backend = await backendResponse.json();
  let model = null;
  try {
    model = await modelResponse.json();
  } catch {
    model = null;
  }

  return { backend, model };
}

function normalizeErrorPayload(payload) {
  const detail = payload?.detail || payload;
  return {
    message: detail?.error || detail?.message || 'Backend request failed.',
    code: detail?.error_code || 'REQUEST_FAILED'
  };
}

export async function postQuery({ files, query, taskHint = 'auto' }) {
  const formData = new FormData();

  files.forEach((file) => formData.append('files', file));
  formData.append('query', query);
  formData.append('task_hint', taskHint);

  const response = await fetch(`${getApiBaseUrl()}/api/query`, {
    method: 'POST',
    body: formData
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const error = normalizeErrorPayload(payload);
    const err = new Error(error.message);
    err.code = error.code;
    throw err;
  }

  if (!payload?.success) {
    const error = normalizeErrorPayload(payload);
    const err = new Error(error.message);
    err.code = error.code;
    throw err;
  }

  return payload;
}
