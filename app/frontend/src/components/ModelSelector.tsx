/**
 * ModelSelector Component - Select analysis speed/quality mode
 */

import { useState } from 'react';

export type ModelMode = 'fast' | 'standard' | 'deep';

interface ModelSelectorProps {
  value: ModelMode;
  onChange: (mode: ModelMode) => void;
  disabled?: boolean;
}

const modeConfig = {
  fast: {
    label: 'Fast',
    description: 'Quick read on your level',
    baseColor: 'border-emerald-500 text-emerald-700 bg-emerald-50',
    hoverColor: 'hover:bg-emerald-100 hover:border-emerald-600',
    selectedColor: 'border-emerald-600 bg-emerald-100 text-emerald-800 ring-2 ring-offset-2 ring-emerald-500',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  standard: {
    label: 'Standard',
    description: 'The full argument',
    baseColor: 'border-blue-500 text-blue-700 bg-blue-50',
    hoverColor: 'hover:bg-blue-100 hover:border-blue-600',
    selectedColor: 'border-blue-600 bg-blue-100 text-blue-800 ring-2 ring-offset-2 ring-blue-500',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  deep: {
    label: 'Deep',
    description: 'Every gap scrutinized',
    baseColor: 'border-red-700 text-red-700 bg-red-50',
    hoverColor: 'hover:bg-red-100 hover:border-red-800',
    selectedColor: 'border-red-700 bg-red-100 text-red-800 ring-2 ring-offset-2 ring-red-500',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    isDeep: true,
  },
};

const deepStyles = `
  .deep-crimson {
    background: linear-gradient(135deg, #450a0a 0%, #7f1d1d 50%, #991b1b 100%);
    box-shadow: 0 0 8px rgba(127, 29, 29, 0.5);
  }
  .deep-crimson:hover {
    background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 50%, #b91c1c 100%);
    box-shadow: 0 0 12px rgba(153, 27, 27, 0.6);
  }
`;

export function ModelSelector({ value, onChange, disabled }: ModelSelectorProps) {
  const [showWarning, setShowWarning] = useState(false);
  const [pendingMode, setPendingMode] = useState<ModelMode | null>(null);

  const handleClick = (mode: ModelMode) => {
    if (disabled) return;

    if (mode === 'deep' && value !== 'deep') {
      setPendingMode(mode);
      setShowWarning(true);
    } else {
      onChange(mode);
    }
  };

  const confirmDeep = () => {
    if (pendingMode) {
      onChange(pendingMode);
    }
    setShowWarning(false);
    setPendingMode(null);
  };

  const cancelDeep = () => {
    setShowWarning(false);
    setPendingMode(null);
  };

  return (
    <div className="relative">
      <style>{deepStyles}</style>
      <div className="flex flex-col items-start gap-1">
        <div className="flex gap-1.5">
          {(Object.keys(modeConfig) as ModelMode[]).map((mode) => {
            const config = modeConfig[mode];
            const isSelected = value === mode;

            return (
              <button
                key={mode}
                onClick={() => handleClick(mode)}
                disabled={disabled}
                className={`
                  flex items-center gap-1.5 px-3 py-1.5 rounded-md border-2 font-medium text-xs
                  transition-all duration-200 transform
                  ${isSelected ? config.selectedColor : `${config.baseColor} ${config.hoverColor}`}
                  ${!isSelected && !disabled ? 'hover:scale-105 hover:shadow-md' : ''}
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <span className={isSelected ? 'text-orange-600' : ''}>{config.icon}</span>
                <span>{config.label}</span>
              </button>
            );
          })}
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-xs font-medium text-gray-600">Analysis Mode:</span>
          <span className="text-xs text-gray-500">{modeConfig[value].description}</span>
        </div>
      </div>

      {/* Deep Mode Warning Modal */}
      {showWarning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-md mx-4 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Deep Analysis Mode</h3>
                <p className="text-sm text-gray-500">This will be significantly slower</p>
              </div>
            </div>

            <p className="text-gray-600 mb-6">
              Deep mode uses <strong>Gemini 3 Pro</strong> for maximum quality analysis.
              This provides the best results but can take <strong>2-3x longer</strong> than Standard mode.
            </p>

            <div className="flex gap-3 justify-end">
              <button
                onClick={cancelDeep}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmDeep}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
              >
                Enable Deep Mode
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
