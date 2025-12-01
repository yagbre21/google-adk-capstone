/**
 * LoadingState Component - Real-time streaming progress indicator
 */

import type { AgentProgress } from '../types/api';

// Shimmer text animation styles - slow dramatic left to right sweep
const shimmerStyles = `
  @keyframes shimmer-text {
    0% { background-position: 100% center; }
    100% { background-position: -100% center; }
  }
  .shimmer-text {
    background: linear-gradient(
      90deg,
      #1f2937 0%,
      #1f2937 30%,
      #818cf8 45%,
      #c7d2fe 50%,
      #818cf8 55%,
      #1f2937 70%,
      #1f2937 100%
    );
    background-size: 200% auto;
    background-clip: text;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer-text 3.5s ease-in-out infinite;
  }

  @keyframes bounce-dot {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-4px); }
  }
  .bounce-dot {
    display: inline-block;
    animation: bounce-dot 1.4s ease-in-out infinite;
  }
  .bounce-dot:nth-child(1) { animation-delay: 0s; }
  .bounce-dot:nth-child(2) { animation-delay: 0.2s; }
  .bounce-dot:nth-child(3) { animation-delay: 0.4s; }
`;

// Shimmer skeleton component
function ShimmerSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden bg-gray-200 rounded ${className}`}>
      <div
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.9) 50%, transparent 100%)',
          animation: 'shimmer 1.5s ease-in-out infinite',
        }}
      />
    </div>
  );
}

interface LoadingStateProps {
  message?: string;
  progress?: AgentProgress[];
}

// Map agent names to display info
const agentInfo: Record<string, { label: string; icon: string; color: string }> = {
  system: { label: 'System', icon: '🚀', color: 'bg-gray-100 text-gray-700' },
  career_analytics: { label: 'Career Analytics', icon: '📊', color: 'bg-blue-100 text-blue-700' },
  role_breakdown: { label: 'Role Breakdown', icon: '📋', color: 'bg-blue-50 text-blue-600' },
  resume_parser: { label: 'Resume Parser', icon: '📄', color: 'bg-emerald-100 text-emerald-700' },
  level_classifier: { label: 'Level Classifier', icon: '📊', color: 'bg-purple-100 text-purple-700' },
  conservative_evaluator: { label: 'Conservative Evaluator', icon: '🔍', color: 'bg-amber-100 text-amber-700' },
  optimistic_evaluator: { label: 'Optimistic Evaluator', icon: '🚀', color: 'bg-green-100 text-green-700' },
  consensus: { label: 'Consensus Agent', icon: '🤝', color: 'bg-indigo-100 text-indigo-700' },
  exact_match_scout: { label: 'Exact Match Scout', icon: '🎯', color: 'bg-red-100 text-red-700' },
  level_up_scout: { label: 'Level Up Scout', icon: '📈', color: 'bg-orange-100 text-orange-700' },
  stretch_scout: { label: 'Stretch Scout', icon: '⭐', color: 'bg-yellow-100 text-yellow-700' },
  trajectory_scout: { label: 'Trajectory Scout', icon: '🔮', color: 'bg-violet-100 text-violet-700' },
  url_validator: { label: 'URL Validator', icon: '✅', color: 'bg-teal-100 text-teal-700' },
  formatter: { label: 'Formatter', icon: '📝', color: 'bg-pink-100 text-pink-700' },
};

export function LoadingState({
  message = 'Analyzing your resume...',
  progress = []
}: LoadingStateProps) {
  const recentProgress = progress.slice(-6).reverse();
  const hasProgress = progress.length > 0;

  // Calculate rough progress percentage based on expected agents
  const progressPercent = Math.min(95, Math.round((progress.length / 15) * 100));

  return (
    <div className="max-w-2xl mx-auto">
      {/* Inject shimmer animation keyframes */}
      <style>{shimmerStyles}</style>

      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-4">
        <div className="flex items-center gap-4">
          {/* Animated spinner */}
          <div className="relative flex-shrink-0">
            <div className="w-12 h-12 border-4 border-primary-100 rounded-full"></div>
            <div className="w-12 h-12 border-4 border-primary-600 rounded-full animate-spin absolute top-0 left-0 border-t-transparent"></div>
          </div>

          <div className="flex-1">
            <h3 className="text-lg font-semibold">
                <span className="shimmer-text">
                  {message.endsWith('...') ? message.slice(0, -3) : message}
                </span>
                {message.endsWith('...') && (
                  <span className="text-gray-900">
                    <span className="bounce-dot">.</span>
                    <span className="bounce-dot">.</span>
                    <span className="bounce-dot">.</span>
                  </span>
                )}
              </h3>
            <p className="text-sm text-gray-500">
              AI agents are analyzing your experience and finding matches
            </p>
          </div>

          {hasProgress && (
            <div className="text-right">
              <span className="text-2xl font-bold text-primary-600">{progressPercent}%</span>
              <p className="text-xs text-gray-500">{progress.length} events</p>
            </div>
          )}
        </div>

        {/* Progress bar */}
        {hasProgress && (
          <div className="mt-4 h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        )}
      </div>

      {/* Agent Activity Feed */}
      {hasProgress ? (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
              </span>
              <span className="text-sm font-medium text-gray-700">Agent Pipeline Active</span>
            </div>
            <span className="text-xs text-gray-500">Live updates</span>
          </div>

          <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
            {recentProgress.map((p, i) => (
              <ProgressLine
                key={i}
                progress={p}
                isLatest={i === 0}
              />
            ))}
          </div>
        </div>
      ) : (
        /* Shimmer skeleton while waiting for streaming to start */
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-primary-500"></span>
              </span>
              <span className="text-sm font-medium text-gray-700">Initializing agents...</span>
            </div>
          </div>

          <div className="divide-y divide-gray-100">
            {/* Shimmer skeleton rows */}
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="px-4 py-4">
                <div className="flex items-start gap-3">
                  <ShimmerSkeleton className="h-6 w-28 rounded-md" />
                  {i === 1 && <ShimmerSkeleton className="h-6 w-16 rounded-md" />}
                </div>
                <div className="mt-3 space-y-2">
                  <ShimmerSkeleton className="h-4 w-full" />
                  <ShimmerSkeleton className="h-4 w-3/4" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ProgressLine({ progress, isLatest }: { progress: AgentProgress; isLatest: boolean }) {
  const info = agentInfo[progress.agent] || {
    label: progress.agent,
    icon: '🤖',
    color: 'bg-gray-100 text-gray-700'
  };

  // Extract the message content (remove the emoji prefix if present)
  const messageContent = progress.message.replace(/^[^\s]+\s*:\s*/, '');

  return (
    <div className={`px-4 py-3 ${isLatest ? 'bg-primary-50' : 'bg-white'} transition-colors`}>
      <div className="flex items-start gap-3">
        <span className={`flex-shrink-0 px-2 py-1 rounded-md text-xs font-medium ${info.color}`}>
          {info.icon} {info.label}
        </span>
        {isLatest && (
          <span className="flex-shrink-0 px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-700">
            Active
          </span>
        )}
      </div>
      <p className={`mt-2 text-sm ${isLatest ? 'text-gray-900' : 'text-gray-600'} line-clamp-2`}>
        {messageContent || progress.message}
      </p>
    </div>
  );
}

