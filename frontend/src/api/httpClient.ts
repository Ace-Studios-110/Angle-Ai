import axios from 'axios';
import {
  getAccessToken,
  getRefreshToken,
  setSession,
  clearSession,
} from '../utils/tokenUtils';
import { toast } from 'react-toastify';
import type { IRefreshTokenResponse } from '../types/apiTypes';

const BASE = import.meta.env.VITE_API_BASE_URL;

export const ErrorCodes = {
  RATE_LIMIT: 'RATE_LIMIT_EXCEEDED',
  UNAUTHORIZED: 'UNAUTHORIZED',
  INVALID_INPUT: 'INVALID_INPUT',
  SERVER_ERROR: 'SERVER_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
} as const;

const ErrorMessages = {
  [ErrorCodes.RATE_LIMIT]: 'Too many requests. Please wait a moment before trying again.',
  [ErrorCodes.UNAUTHORIZED]: 'Session expired. Please log in again.',
  [ErrorCodes.INVALID_INPUT]: 'Invalid request. Please check your input.',
  [ErrorCodes.SERVER_ERROR]: 'Server error. Please try again later.',
  [ErrorCodes.NETWORK_ERROR]: 'Network error. Please check your connection.',
} as const;

function isAxiosError(error: any): boolean {
  return error && error.isAxiosError === true;
}

const handleError = (error: any): never => {
  if (isAxiosError(error)) {
    const { response } = error;
    const status = response?.status;
    const errorCode = response?.data?.code;

    if (errorCode === ErrorCodes.RATE_LIMIT) {
      toast.error(ErrorMessages[ErrorCodes.RATE_LIMIT]);
      throw new Error(ErrorMessages[ErrorCodes.RATE_LIMIT]);
    }

    switch (status) {
      case 400:
        toast.error(response?.data?.error || ErrorMessages[ErrorCodes.INVALID_INPUT]);
        break;
      case 429:
        toast.error(ErrorMessages[ErrorCodes.RATE_LIMIT]);
        break;
      case 500:
        toast.error(ErrorMessages[ErrorCodes.SERVER_ERROR]);
        break;
      default:
        if (!navigator.onLine) {
          toast.error(ErrorMessages[ErrorCodes.NETWORK_ERROR]);
        } else {
          toast.error(ErrorMessages[ErrorCodes.SERVER_ERROR]);
        }
    }
  } else {
    toast.error('An unexpected error occurred. Please try again.');
  }

  throw error;
};

const httpClient = axios.create({
  baseURL: BASE,
});

// Request Interceptor
httpClient.interceptors.request.use(
  config => {
    const token = getAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Refresh logic
let isRefreshing = false;
let failedQueue: {
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) prom.reject(error);
    else prom.resolve(token);
  });
  failedQueue = [];
};

httpClient.interceptors.response.use(
  response => response,
  async error => {
    console.log('--- Axios Error:', error);
    console.log('--- Error Response:', error?.response?.data);
    console.log('--- Error Status:', error?.response?.status);
    
    const originalRequest = error.config;

    const is401 = error?.response?.status === 401;
    const isRetry = originalRequest && originalRequest._retry;

    if (is401 && !isRetry) {
      console.log('--- Attempting token refresh...');
      originalRequest._retry = true;

      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        console.log('--- No refresh token found, redirecting to login');
        toast.error(ErrorMessages[ErrorCodes.UNAUTHORIZED]);
        clearSession();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        console.log('--- Token refresh already in progress, queuing request');
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          if (token && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return httpClient(originalRequest);
        });
      }

      isRefreshing = true;
      console.log('--- Starting token refresh...');

      try {
        const res = await axios.post<IRefreshTokenResponse>(`${BASE}/auth/refresh-token`, {
          refresh_token: refreshToken,
        });

        const session = res.data?.result?.session;
        if (!session) throw new Error('Invalid session from refresh');

        const { access_token, refresh_token: newRefreshToken } = session;
        setSession(access_token, newRefreshToken);

        httpClient.defaults.headers.common.Authorization = `Bearer ${access_token}`;
        processQueue(null, access_token);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        console.log('--- Token refresh successful, retrying original request');
        // Remove the window.location.reload() call to prevent infinite loops
        return httpClient(originalRequest);
      } catch (refreshErr) {
        console.log('--- Token refresh failed:', refreshErr);
        processQueue(refreshErr, null);
        toast.error(ErrorMessages[ErrorCodes.UNAUTHORIZED]);
        clearSession();
        window.location.href = '/login';
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    return handleError(error);
  }
);

export default httpClient;
