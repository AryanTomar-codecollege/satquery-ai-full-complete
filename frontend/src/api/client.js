
const DEFAULT_API_BASE = 'http://127.0.0.1:8001';

export function getApiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE).replace(/\/+$/, '');
}

export async function healthCheck() {
  const base = getApiBaseUrl();
  const backendResponse = await fetch(`${base}/health`);
  const modelResponse = await fetch(`${base}/api/model/health`);

  if (!backendResponse.ok) {
    throw new Error(`Backend health check failed (${backendResponse.status}).`);
  }

  const backend = await backendResponse.json();
  let model = null;
  try { model = await modelResponse.json(); } catch {}

  return { backend, model };
}

function errorFromPayload(payload) {
  const detail = payload?.detail ?? payload;
  return {
    message: detail?.error || detail?.message || 'Backend request failed.',
    code: detail?.error_code || 'REQUEST_FAILED'
  };
}

export async function postQuery({ files, query, taskHint = 'auto' }) {
  if (!Array.isArray(files) || files.length < 1) {
    throw new Error('Upload at least one GeoTIFF.');
  }
  if (files.length > 2) {
    throw new Error('A maximum of 2 GeoTIFF files is supported.');
  }

  const formData = new FormData();
  files.forEach(file => formData.append('files', file, file.name));
  formData.append('query', query.trim());
  formData.append('task_hint', taskHint || 'auto');

  let response;
  try {
    response = await fetch(`${getApiBaseUrl()}/api/query`, {
      method: 'POST',
      body: formData
    });
  } catch {
    const err = new Error(`Cannot reach FastAPI at ${getApiBaseUrl()}.`);
    err.code = 'BACKEND_UNREACHABLE';
    throw err;
  }

  let payload = null;
  try { payload = await response.json(); } catch {}

  if (!response.ok) {
    const error = errorFromPayload(payload);
    const err = new Error(error.message);
    err.code = error.code;
    throw err;
  }

  if (!payload?.success) {
    const error = errorFromPayload(payload);
    const err = new Error(error.message);
    err.code = error.code;
    throw err;
  }

  return payload;
}
