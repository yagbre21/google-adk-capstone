/**
 * API Service - Handles all backend communication
 */

import type { AnalysisResponse, RefineResponse, HealthResponse, ErrorResponse, StreamEvent } from '../types/api';

const API_BASE = '/api/v1';

class ApiError extends Error {
  constructor(public status: number, message: string, public code?: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ErrorResponse = await response.json().catch(() => ({
      status: 'error',
      detail: `HTTP ${response.status}: ${response.statusText}`
    }));
    throw new ApiError(response.status, error.detail, error.code);
  }
  return response.json();
}

/**
 * Parse SSE stream and yield events
 */
async function* parseSSEStream(response: Response): AsyncGenerator<StreamEvent> {
  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event: StreamEvent = JSON.parse(line.slice(6));
          yield event;
        } catch {
          // Skip malformed JSON
        }
      }
    }
  }
}

export const apiService = {
  /**
   * Check API health
   */
  async health(): Promise<HealthResponse> {
    const response = await fetch(`${API_BASE}/health`);
    return handleResponse<HealthResponse>(response);
  },

  /**
   * Analyze resume from file upload
   */
  async analyzeFile(file: File): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    });

    return handleResponse<AnalysisResponse>(response);
  },

  /**
   * Analyze resume from pasted text
   */
  async analyzeText(resumeText: string): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append('resume_text', resumeText);

    const response = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      body: formData,
    });

    return handleResponse<AnalysisResponse>(response);
  },

  /**
   * Refine job recommendations
   */
  async refine(sessionId: string, feedback: string): Promise<RefineResponse> {
    const response = await fetch(`${API_BASE}/refine`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        feedback: feedback,
      }),
    });

    return handleResponse<RefineResponse>(response);
  },

  /**
   * Analyze resume from file with streaming progress
   */
  async *analyzeFileStream(file: File, modelMode: string = 'standard'): AsyncGenerator<StreamEvent> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('model_mode', modelMode);

    const response = await fetch(`${API_BASE}/analyze/stream`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(response.status, `HTTP ${response.status}: ${response.statusText}`);
    }

    yield* parseSSEStream(response);
  },

  /**
   * Analyze resume from text with streaming progress
   */
  async *analyzeTextStream(resumeText: string, modelMode: string = 'standard'): AsyncGenerator<StreamEvent> {
    const formData = new FormData();
    formData.append('resume_text', resumeText);
    formData.append('model_mode', modelMode);

    const response = await fetch(`${API_BASE}/analyze/stream`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new ApiError(response.status, `HTTP ${response.status}: ${response.statusText}`);
    }

    yield* parseSSEStream(response);
  },

  /**
   * Refine with streaming progress
   */
  async *refineStream(sessionId: string, feedback: string): AsyncGenerator<StreamEvent> {
    const response = await fetch(`${API_BASE}/refine/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        feedback: feedback,
      }),
    });

    if (!response.ok) {
      throw new ApiError(response.status, `HTTP ${response.status}: ${response.statusText}`);
    }

    yield* parseSSEStream(response);
  },
};

export { ApiError };
