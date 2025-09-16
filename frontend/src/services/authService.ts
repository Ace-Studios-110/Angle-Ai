
import axios from 'axios';
import httpClient from '../api/httpClient';
import type { AngelResponse, APIResponse, ChatResponse, IGeneratedBP, IRecentChats } from '../types/apiTypes';

const BASE = import.meta.env.VITE_API_BASE_URL as string; // e.g. "/api/v1/auth"

interface Session {
    access_token: string;
    refresh_token: string;
    user: {
        id: string;
        email: string;
        [key: string]: any;
    };
    [key: string]: any;
}

interface AuthResponse {
    session: Session;
    [key: string]: any;
}

interface ErrorResponse {
    response: { data: { error: string } };
}

export async function signUp({
    email,
    password,
}: {
    email: string;
    password: string;
}): Promise<void> {
    await axios.post<void>(`${BASE}/auth/signup`, { email, password });
}

export async function signIn({
    email,
    password,
}: {
    email: string;
    password: string;
}): Promise<Session> {
    try {
        const { data } = await axios.post<AuthResponse>(`${BASE}/auth/signin`, {
            email,
            password,
        });

        return data.result.session;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error ||
            'Signin failed';
        throw new Error(message);
    }
}

export async function resetPassword({
    email,
}: {
    email: string;
}): Promise<void> {
    try {
        await axios.post<void>(`${BASE}/auth/reset-password`, { email });
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error ||
            'Reset password failed';
        throw new Error(message);
    }
}

export async function createSessions(title: string): Promise<IRecentChats> {
    const token = localStorage.getItem('sb_access_token');
    if (!token) throw new Error('Not authenticated');

    try {
        const { data } = await httpClient.post<APIResponse<IRecentChats>>(
            `${BASE}/angel/sessions`,
            { title },
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return data.result;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error || 'Session request failed';
        throw new Error(message);
    }
}

export async function fetchSessions(): Promise<IRecentChats> {
    const token = localStorage.getItem('sb_access_token');
    if (!token) throw new Error('Not authenticated');

    try {
        const { data } = await httpClient.get<APIResponse<IRecentChats>>(
            `${BASE}/angel/sessions`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return data.result;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error || 'Session request failed';
        throw new Error(message);
    }
}

export async function fetchQuestion(
    content: string,
    sessionId: string
): Promise<AngelResponse> {
    const token = localStorage.getItem('sb_access_token');
    if (!token) throw new Error('Not authenticated');

    try {
        const { data } = await httpClient.post<AngelResponse>(
            `${BASE}/angel/sessions/${sessionId}/chat`,
            { content },
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return data;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error || 'Chat request failed';
        throw new Error(message);
    }
}

export async function fetchBusinessPlan(
    sessionId: string
): Promise<IGeneratedBP> {
    const token = localStorage.getItem('sb_access_token');
    if (!token) throw new Error('Not authenticated');

    try {
        const { data } = await httpClient.post<IGeneratedBP>(
            `${BASE}/angel/sessions/${sessionId}/generate-plan`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return data;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error || 'Chat request failed';
        throw new Error(message);
    }
}

export async function fetchRoadmapPlan(
    sessionId: string
): Promise<IGeneratedBP> {
    const token = localStorage.getItem('sb_access_token');
    if (!token) throw new Error('Not authenticated');

    try {
        const { data } = await httpClient.get<IGeneratedBP>(
            `${BASE}/angel/sessions/${sessionId}/roadmap-plan`,
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return data;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error || 'Chat request failed';
        throw new Error(message);
    }
}

export async function uploadBusinessPlan(
    sessionId: string,
    file: File
): Promise<{ success: boolean; message?: string; error?: string; chat_message?: string }> {
    const token = localStorage.getItem('sb_access_token');
    if (!token) throw new Error('Not authenticated');

    const formData = new FormData();
    formData.append('file', file);

    try {
        const { data } = await httpClient.post<{ success: boolean; message?: string; error?: string; chat_message?: string }>(
            `${BASE}/angel/sessions/${sessionId}/upload-business-plan`,
            formData,
            { 
                headers: { 
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'multipart/form-data'
                } 
            }
        );
        return data;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error || 'Upload failed';
        throw new Error(message);
    }
}

export async function fetchNextQuestion(
    userMessage: string,
    contextData: { phase: 'kyc'; stepIndex: number; skipStep?: boolean }
): Promise<ChatResponse> {
    const token = localStorage.getItem('sb_access_token');
    if (!token) throw new Error('Not authenticated');

    try {
        const { data } = await httpClient.post<ChatResponse>(
            `${BASE}/angel/chat`,
            { userMessage, contextData },
            { headers: { Authorization: `Bearer ${token}` } }
        );
        return data;
    } catch (err) {
        const message = (err as ErrorResponse).response?.data.error || 'Chat request failed';
        throw new Error(message);
    }
}
