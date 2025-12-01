/**
 * API Types - Matches backend schemas
 */

export interface AnalysisResponse {
  status: 'success' | 'error';
  session_id: string;
  result: string;
  processing_time_ms: number;
}

export interface RefineResponse {
  status: 'success' | 'error';
  session_id: string;
  result: string;
  processing_time_ms: number;
}

export interface ErrorResponse {
  status: 'error';
  detail: string;
  code?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

/**
 * SSE Streaming Types
 */
export interface StreamEvent {
  type: 'progress' | 'result' | 'error';
  agent?: string;
  message?: string;
  result?: string;
  session_id?: string;
  processing_time_ms?: number;
}

export interface AgentProgress {
  agent: string;
  message: string;
  timestamp: number;
}
