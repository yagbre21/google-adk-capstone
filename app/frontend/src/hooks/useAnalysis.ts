/**
 * useAnalysis Hook - Manages analysis state and operations with streaming progress
 */

import { useState, useCallback } from 'react';
import { apiService, ApiError } from '../services/api';
import type { AnalysisResponse, AgentProgress } from '../types/api';
import type { ModelMode } from '../components/ModelSelector';

export type AnalysisState =
  | { status: 'idle' }
  | { status: 'analyzing'; progress: AgentProgress[] }
  | { status: 'refining'; progress: AgentProgress[] }
  | { status: 'success'; data: AnalysisResponse }
  | { status: 'error'; error: string };

export interface RefinementInfo {
  isRefined: boolean;
  query: string;
  refinedAt: number;
}

export interface HistoryEntry {
  data: AnalysisResponse;
  refinementInfo: RefinementInfo | null;
  timestamp: number;
}

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>({ status: 'idle' });
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [progress, setProgress] = useState<AgentProgress[]>([]);
  const [refinementInfo, setRefinementInfo] = useState<RefinementInfo | null>(null);

  // Result history for navigation
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyIndex, setHistoryIndex] = useState<number>(-1);

  const addProgress = useCallback((agent: string, message: string) => {
    const newProgress: AgentProgress = {
      agent,
      message,
      timestamp: Date.now()
    };
    setProgress(prev => [...prev, newProgress]);
    return newProgress;
  }, []);

  const analyzeFile = useCallback(async (file: File, modelMode: ModelMode = 'standard') => {
    setProgress([]);
    setRefinementInfo(null); // Clear any previous refinement
    setHistory([]); // Clear history for new analysis
    setHistoryIndex(-1);
    setState({ status: 'analyzing', progress: [] });

    try {
      let result: AnalysisResponse | null = null;

      for await (const event of apiService.analyzeFileStream(file, modelMode)) {
        if (event.type === 'progress' && event.agent && event.message) {
          const newProgress = addProgress(event.agent, event.message);
          setState(prev => {
            if (prev.status === 'analyzing') {
              return { ...prev, progress: [...prev.progress, newProgress] };
            }
            return prev;
          });
        } else if (event.type === 'result') {
          result = {
            status: 'success',
            session_id: event.session_id || '',
            result: event.result || '',
            processing_time_ms: event.processing_time_ms || 0
          };
          setSessionId(result.session_id);
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Analysis failed');
        }
      }

      if (result) {
        // Add to history
        const entry: HistoryEntry = {
          data: result,
          refinementInfo: null,
          timestamp: Date.now()
        };
        setHistory([entry]);
        setHistoryIndex(0);
        setState({ status: 'success', data: result });
        return result;
      } else {
        throw new Error('No result received');
      }
    } catch (error) {
      const message = error instanceof ApiError ? error.message : (error as Error).message || 'Analysis failed';
      setState({ status: 'error', error: message });
      throw error;
    }
  }, [addProgress]);

  const analyzeText = useCallback(async (text: string, modelMode: ModelMode = 'standard') => {
    setProgress([]);
    setRefinementInfo(null); // Clear any previous refinement
    setHistory([]); // Clear history for new analysis
    setHistoryIndex(-1);
    setState({ status: 'analyzing', progress: [] });

    try {
      let result: AnalysisResponse | null = null;

      for await (const event of apiService.analyzeTextStream(text, modelMode)) {
        if (event.type === 'progress' && event.agent && event.message) {
          const newProgress = addProgress(event.agent, event.message);
          setState(prev => {
            if (prev.status === 'analyzing') {
              return { ...prev, progress: [...prev.progress, newProgress] };
            }
            return prev;
          });
        } else if (event.type === 'result') {
          result = {
            status: 'success',
            session_id: event.session_id || '',
            result: event.result || '',
            processing_time_ms: event.processing_time_ms || 0
          };
          setSessionId(result.session_id);
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Analysis failed');
        }
      }

      if (result) {
        // Add to history
        const entry: HistoryEntry = {
          data: result,
          refinementInfo: null,
          timestamp: Date.now()
        };
        setHistory([entry]);
        setHistoryIndex(0);
        setState({ status: 'success', data: result });
        return result;
      } else {
        throw new Error('No result received');
      }
    } catch (error) {
      const message = error instanceof ApiError ? error.message : (error as Error).message || 'Analysis failed';
      setState({ status: 'error', error: message });
      throw error;
    }
  }, [addProgress]);

  const refine = useCallback(async (feedback: string) => {
    if (!sessionId) {
      throw new Error('No active session');
    }

    setProgress([]);
    setState({ status: 'refining', progress: [] });

    try {
      let result: AnalysisResponse | null = null;

      for await (const event of apiService.refineStream(sessionId, feedback)) {
        if (event.type === 'progress' && event.agent && event.message) {
          const newProgress = addProgress(event.agent, event.message);
          setState(prev => {
            if (prev.status === 'refining') {
              return { ...prev, progress: [...prev.progress, newProgress] };
            }
            return prev;
          });
        } else if (event.type === 'result') {
          result = {
            status: 'success',
            session_id: sessionId,
            result: event.result || '',
            processing_time_ms: event.processing_time_ms || 0
          };
        } else if (event.type === 'error') {
          throw new Error(event.message || 'Refinement failed');
        }
      }

      if (result) {
        // Create refinement info for this result
        const newRefinementInfo: RefinementInfo = {
          isRefined: true,
          query: feedback,
          refinedAt: Date.now()
        };

        // Add to history (append new refinement)
        const entry: HistoryEntry = {
          data: result,
          refinementInfo: newRefinementInfo,
          timestamp: Date.now()
        };
        setHistory(prev => [...prev, entry]);
        setHistoryIndex(prev => prev + 1);

        setState({ status: 'success', data: result });
        setRefinementInfo(newRefinementInfo);
        return result;
      } else {
        throw new Error('No result received');
      }
    } catch (error) {
      const message = error instanceof ApiError ? error.message : (error as Error).message || 'Refinement failed';
      setState({ status: 'error', error: message });
      throw error;
    }
  }, [sessionId, addProgress]);

  // Navigation functions for result history
  const goToPrev = useCallback(() => {
    if (historyIndex > 0) {
      const newIndex = historyIndex - 1;
      const entry = history[newIndex];
      setHistoryIndex(newIndex);
      setState({ status: 'success', data: entry.data });
      setRefinementInfo(entry.refinementInfo);
    }
  }, [historyIndex, history]);

  const goToNext = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const newIndex = historyIndex + 1;
      const entry = history[newIndex];
      setHistoryIndex(newIndex);
      setState({ status: 'success', data: entry.data });
      setRefinementInfo(entry.refinementInfo);
    }
  }, [historyIndex, history]);

  const reset = useCallback(() => {
    setState({ status: 'idle' });
    setSessionId(null);
    setProgress([]);
    setRefinementInfo(null);
    setHistory([]);
    setHistoryIndex(-1);
  }, []);

  return {
    state,
    sessionId,
    progress,
    refinementInfo,
    analyzeFile,
    analyzeText,
    refine,
    reset,
    // History navigation
    history,
    historyIndex,
    goToPrev,
    goToNext,
    canGoBack: historyIndex > 0,
    canGoForward: historyIndex < history.length - 1,
    isLoading: state.status === 'analyzing' || state.status === 'refining',
    isSuccess: state.status === 'success',
    isError: state.status === 'error',
  };
}
