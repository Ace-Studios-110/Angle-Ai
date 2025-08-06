import { toast } from 'react-toastify';
import { clearSession } from './tokenUtils';

export const ErrorCodes = {
  RATE_LIMIT: 'RATE_LIMIT_EXCEEDED',
  UNAUTHORIZED: 'UNAUTHORIZED',
  INVALID_INPUT: 'INVALID_INPUT',
  SERVER_ERROR: 'SERVER_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR'
} as const;

const ErrorMessages = {
  [ErrorCodes.RATE_LIMIT]: 'Too many requests. Please wait a moment before trying again.',
  [ErrorCodes.UNAUTHORIZED]: 'Session expired. Please log in again.',
  [ErrorCodes.INVALID_INPUT]: 'Invalid request. Please check your input.',
  [ErrorCodes.SERVER_ERROR]: 'Server error. Please try again later.',
  [ErrorCodes.NETWORK_ERROR]: 'Network error. Please check your connection.'
} as const;

function isAxiosError(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as any).isAxiosError === true
  );
}

export function handleApiError(error: unknown): never {
  if (isAxiosError(error)) {
    const status = (error as any).response?.status;
    const errorCode = (error as any).response?.data?.code;

    if (errorCode === ErrorCodes.RATE_LIMIT) {
      toast.error(ErrorMessages[ErrorCodes.RATE_LIMIT]);
      throw new Error(ErrorMessages[ErrorCodes.RATE_LIMIT]);
    }

    switch (status) {
      case 401:
        toast.error(ErrorMessages[ErrorCodes.UNAUTHORIZED]);
        clearSession();
        window.location.href = '/login';
        throw new Error(ErrorMessages[ErrorCodes.UNAUTHORIZED]);
      case 400:
        toast.error((error as any).response?.data?.error || ErrorMessages[ErrorCodes.INVALID_INPUT]);
        throw new Error((error as any).response?.data?.error || ErrorMessages[ErrorCodes.INVALID_INPUT]);
      case 429:
        toast.error(ErrorMessages[ErrorCodes.RATE_LIMIT]);
        throw new Error(ErrorMessages[ErrorCodes.RATE_LIMIT]);
      case 500:
        toast.error(ErrorMessages[ErrorCodes.SERVER_ERROR]);
        throw new Error(ErrorMessages[ErrorCodes.SERVER_ERROR]);
      default:
        if (!navigator.onLine) {
          toast.error(ErrorMessages[ErrorCodes.NETWORK_ERROR]);
          throw new Error(ErrorMessages[ErrorCodes.NETWORK_ERROR]);
        }
        toast.error(ErrorMessages[ErrorCodes.SERVER_ERROR]);
        throw new Error(ErrorMessages[ErrorCodes.SERVER_ERROR]);
    }
  }
  toast.error('An unexpected error occurred. Please try again.');
  throw error;
}
