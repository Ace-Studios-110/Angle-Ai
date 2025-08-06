import type { AuthResponse, Session } from '../types/apiTypes';
import httpClient from './httpClient';

interface ErrorResponse {
  response: { data: { error: string } };
}

export async function signUp({ email, password }: { email: string; password: string }): Promise<void> {
  await httpClient.post('/auth/signup', { email, password });
}

export async function signIn({ email, password }: { email: string; password: string }): Promise<Session> {
  try {
    const { data } = await httpClient.post<AuthResponse>('/auth/signin', { email, password });
    return data.result.session;
  } catch (err: any) {
    const message = err.message || 'Signin failed';
    throw new Error(message);
  }
}

export async function resetPassword({ email }: { email: string }): Promise<void> {
  try {
    await httpClient.post('/auth/reset-password', { email });
  } catch (err) {
    const message = (err as ErrorResponse).response?.data.error || 'Reset password failed';
    throw new Error(message);
  }
}

export interface ChatResponse {
  success: boolean;
  message: string;
  result: {
    angelReply: string;
  };
}

export async function fetchNextQuestion(
  userMessage: string,
  contextData: { phase: 'kyc'; stepIndex: number }
): Promise<ChatResponse> {
  try {
    const { data } = await httpClient.post<ChatResponse>('/angel/chat', { userMessage, contextData });
    return data;
  } catch (err) {
    const message = (err as ErrorResponse).response?.data.error || 'Chat request failed';
    throw new Error(message);
  }
}
