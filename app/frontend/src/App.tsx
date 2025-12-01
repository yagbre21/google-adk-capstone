/**
 * Main App Component
 */

import { useState, useEffect } from 'react';
import { useAnalysis } from './hooks/useAnalysis';
import { ResumeUpload } from './components/ResumeUpload';
import { LoadingState } from './components/LoadingState';
import { ResultDisplay } from './components/ResultDisplay';
import { ErrorDisplay } from './components/ErrorDisplay';
import { ModelSelector, type ModelMode } from './components/ModelSelector';
import { ExampleModal } from './components/ExampleModal';

const getInitialModelMode = (): ModelMode => {
  const saved = sessionStorage.getItem('modelMode');
  if (saved === 'fast' || saved === 'standard' || saved === 'deep') {
    return saved;
  }
  return 'standard';
};

export default function App() {
  const [modelMode, setModelMode] = useState<ModelMode>(getInitialModelMode);
  const [showExample, setShowExample] = useState(false);

  useEffect(() => {
    sessionStorage.setItem('modelMode', modelMode);
  }, [modelMode]);
  const {
    state,
    analyzeFile,
    analyzeText,
    refine,
    reset,
    isLoading,
    refinementInfo,
    historyIndex,
    history,
    goToPrev,
    goToNext,
    canGoBack,
    canGoForward,
  } = useAnalysis();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Agentic Job Search Recommender</h1>
              <p className="text-xs text-gray-500">AI-powered career recommendations</p>
            </div>
          </div>

          <ModelSelector
            value={modelMode}
            onChange={setModelMode}
            disabled={isLoading}
          />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-12">
        {/* Hero Section - Only show on idle */}
        {state.status === 'idle' && (
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              100 jobs shouldn't need 100 rewrites!
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-4">
              AI agents debate your level, reach consensus, then find jobs that fit you. Not the other way around.
            </p>
            <button
              onClick={() => setShowExample(true)}
              className="text-primary-600 hover:text-primary-700 text-sm font-medium inline-flex items-center gap-1 hover:underline"
            >
              See example results
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}

        {/* Content based on state */}
        {state.status === 'idle' && (
          <ResumeUpload
            onFileUpload={(file) => analyzeFile(file, modelMode)}
            onTextSubmit={(text) => analyzeText(text, modelMode)}
            isLoading={false}
          />
        )}

        {state.status === 'analyzing' && (
          <LoadingState
            message="Analyzing your resume..."
            progress={state.progress}
          />
        )}

        {state.status === 'refining' && (
          <LoadingState
            message="Refining your recommendations..."
            progress={state.progress}
          />
        )}

        {state.status === 'success' && (
          <ResultDisplay
            result={state.data.result}
            processingTime={state.data.processing_time_ms}
            onRefine={refine}
            onReset={reset}
            isRefining={isLoading}
            refinementInfo={refinementInfo}
            historyIndex={historyIndex}
            historyLength={history.length}
            onPrev={goToPrev}
            onNext={goToNext}
            canGoBack={canGoBack}
            canGoForward={canGoForward}
          />
        )}

        {state.status === 'error' && (
          <ErrorDisplay
            message={state.error}
            onRetry={reset}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white mt-auto">
        <div className="max-w-6xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
          <p>
            Created by <span className="font-semibold text-gray-700">Yves Agbre</span> |{' '}
            <a
              href="https://www.linkedin.com/in/yagbre/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              LinkedIn
            </a>
            {' | '}
            <a
              href="https://github.com/yagbre21/google-adk-capstone"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              GitHub
            </a>
            {' · '}
            Built with Google ADK and Gemini for the{' '}
            <a
              href="https://www.kaggle.com/competitions/agents-intensive-capstone-project"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-600 hover:underline"
            >
              Kaggle Agents Intensive Capstone
            </a>
          </p>
        </div>
      </footer>

      {/* Example Modal */}
      <ExampleModal isOpen={showExample} onClose={() => setShowExample(false)} />
    </div>
  );
}
