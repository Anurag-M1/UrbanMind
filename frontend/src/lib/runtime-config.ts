const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '');

const apiBaseEnv = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
const wsEnv = (import.meta.env.VITE_WS_URL as string | undefined)?.trim();

export const API_BASE_URL = apiBaseEnv ? trimTrailingSlash(apiBaseEnv) : '';

export const WS_DASHBOARD_URL = wsEnv
  ? wsEnv
  : API_BASE_URL
    ? `${API_BASE_URL.replace(/^http/, 'ws')}/ws/dashboard`
    : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.hostname}:8000/ws/dashboard`;

export const buildApiUrl = (path: string) => {
  if (!API_BASE_URL) {
    return path;
  }
  return `${API_BASE_URL}${path}`;
};
