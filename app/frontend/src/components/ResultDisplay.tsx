/**
 * ResultDisplay Component - Renders analysis results with polished styling and collapsible sections
 */

import { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';

interface RefinementInfo {
  isRefined: boolean;
  query: string;
  refinedAt: number;
}

interface ResultDisplayProps {
  result: string;
  processingTime: number;
  onRefine: (feedback: string) => void;
  onReset: () => void;
  isRefining: boolean;
  refinementInfo?: RefinementInfo | null;
  // History navigation
  historyIndex: number;
  historyLength: number;
  onPrev: () => void;
  onNext: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
}

// Section styling based on emoji/title
const getSectionInfo = (text: string) => {
  const textStr = String(text);
  if (textStr.includes('RESUME ANALYSIS')) {
    return { style: 'bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500', key: 'resume' };
  }
  if (textStr.includes('LEVEL CLASSIFICATION')) {
    return { style: 'bg-gradient-to-r from-purple-50 to-violet-50 border-l-4 border-purple-500', key: 'level' };
  }
  if (textStr.includes('EXACT MATCH')) {
    return { style: 'bg-gradient-to-r from-emerald-50 to-green-50 border-l-4 border-emerald-500', key: 'exact' };
  }
  if (textStr.includes('LEVEL UP')) {
    return { style: 'bg-gradient-to-r from-orange-50 to-amber-50 border-l-4 border-orange-500', key: 'levelup' };
  }
  if (textStr.includes('STRETCH')) {
    return { style: 'bg-gradient-to-r from-red-50 to-rose-50 border-l-4 border-red-500', key: 'stretch' };
  }
  if (textStr.includes('TRAJECTORY')) {
    return { style: 'bg-gradient-to-r from-violet-50 to-purple-50 border-l-4 border-violet-500', key: 'trajectory' };
  }
  if (textStr.includes('REFINE')) {
    return { style: 'bg-gradient-to-r from-gray-50 to-slate-50 border-l-4 border-gray-400', key: 'refine' };
  }
  return { style: 'bg-gray-50 border-l-4 border-gray-300', key: 'other' };
};

// Check if line is a decorative separator (Unicode box-drawing or dashes)
const isDecorativeLine = (line: string) => {
  const trimmed = line.trim();
  // Match lines that are only box-drawing chars, dashes, or equals
  return /^[━─═\-_=]{3,}$/.test(trimmed) || trimmed === '---' || trimmed === '***';
};

// Parse result into sections
const parseIntoSections = (markdown: string) => {
  const sections: { title: string; content: string; key: string }[] = [];
  const lines = markdown.split('\n');
  let currentSection: { title: string; content: string[]; key: string } | null = null;

  for (const line of lines) {
    // Skip decorative separator lines
    if (isDecorativeLine(line)) {
      continue;
    }

    if (line.startsWith('## ')) {
      if (currentSection) {
        sections.push({
          title: currentSection.title,
          content: currentSection.content.join('\n'),
          key: currentSection.key
        });
      }
      const title = line.substring(3);
      const info = getSectionInfo(title);
      currentSection = { title, content: [], key: info.key };
    } else if (currentSection) {
      currentSection.content.push(line);
    }
  }

  if (currentSection) {
    sections.push({
      title: currentSection.title,
      content: currentSection.content.join('\n'),
      key: currentSection.key
    });
  }

  return sections;
};

// Collapsible Section Component
function CollapsibleSection({
  title,
  content,
  isExpanded,
  onToggle
}: {
  title: string;
  content: string;
  sectionKey: string;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const { style } = getSectionInfo(title);

  return (
    <div className={`${isExpanded ? '' : 'mb-2'}`}>
      <button
        onClick={onToggle}
        className={`w-full text-left px-6 md:px-8 py-4 ${style} flex items-center justify-between hover:opacity-90 transition-opacity rounded-lg shadow-md hover:shadow-lg`}
      >
        <h2 className="text-xl font-bold text-gray-900 m-0 flex items-center gap-2">
          {title}
        </h2>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-6 md:px-8 py-4 prose prose-sm max-w-none">
          <ReactMarkdown
            components={{
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold text-gray-800 mt-4 mb-3 pb-2 border-b border-gray-100 first:mt-0">
                  {children}
                </h3>
              ),
              p: ({ children }) => (
                <p className="text-gray-700 mb-4 leading-relaxed">{children}</p>
              ),
              strong: ({ children }) => (
                <strong className="font-semibold text-gray-900">{children}</strong>
              ),
              ul: ({ children }) => (
                <ul className="space-y-2 mb-4 ml-1">{children}</ul>
              ),
              li: ({ children }) => (
                <li className="text-gray-700 flex items-start gap-2">
                  <span className="text-primary-500 mt-1.5 text-xs">●</span>
                  <span>{children}</span>
                </li>
              ),
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium no-underline hover:underline bg-blue-50 px-2 py-0.5 rounded"
                >
                  {children}
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-primary-300 bg-primary-50 pl-4 py-2 my-4 italic text-gray-700 rounded-r">
                  {children}
                </blockquote>
              ),
              hr: () => null, // Hide horizontal rules - sections have their own styling
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export function ResultDisplay({
  result,
  processingTime,
  onRefine,
  onReset,
  isRefining,
  refinementInfo,
  historyIndex,
  historyLength,
  onPrev,
  onNext,
  canGoBack,
  canGoForward
}: ResultDisplayProps) {
  const [feedback, setFeedback] = useState('');

  // Parse result into sections (filter out the REFINE section - we have our own UI)
  const sections = useMemo(() =>
    parseIntoSections(result).filter(s => s.key !== 'refine'),
    [result]
  );

  // Track expanded sections (all expanded by default)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(() => {
    return new Set(sections.map(s => s.key));
  });

  const toggleSection = (key: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const expandAll = () => {
    setExpandedSections(new Set(sections.map(s => s.key)));
  };

  const collapseAll = () => {
    setExpandedSections(new Set());
  };

  const handleRefine = () => {
    if (feedback.trim().length >= 3) {
      onRefine(feedback.trim());
      setFeedback('');
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Your Results</h2>
          <p className="text-sm text-gray-500">
            Processed in {(processingTime / 1000).toFixed(1)}s
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* History navigation - only show when there's history */}
          {historyLength > 1 && (
            <div className="flex items-center gap-1 mr-2 pr-2 border-r border-gray-200">
              <button
                onClick={onPrev}
                disabled={!canGoBack}
                className="px-2 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Prev
              </button>
              <span className="text-xs text-gray-400 px-1">
                {historyIndex + 1}/{historyLength}
              </span>
              <button
                onClick={onNext}
                disabled={!canGoForward}
                className="px-2 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
              >
                Next
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          )}
          <button
            onClick={collapseAll}
            className="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
          >
            Collapse All
          </button>
          <button
            onClick={expandAll}
            className="px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Analyze Another Resume
          </button>
        </div>
      </div>

      {/* Refinement Banner */}
      {refinementInfo?.isRefined && (
        <div className="mb-6 bg-gradient-to-r from-primary-50 to-indigo-50 border border-primary-200 rounded-lg p-4 flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-primary-800">
              Results Refined
            </p>
            <p className="text-sm text-primary-600 mt-0.5">
              Filtered by: <span className="font-medium">"{refinementInfo.query}"</span>
            </p>
          </div>
        </div>
      )}

      {/* Results Card with Collapsible Sections */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden p-3">
        {sections.length > 0 ? (
          sections.map((section) => (
            <CollapsibleSection
              key={section.key}
              title={section.title}
              content={section.content}
              sectionKey={section.key}
              isExpanded={expandedSections.has(section.key)}
              onToggle={() => toggleSection(section.key)}
            />
          ))
        ) : (
          <div className="p-6 md:p-8 prose prose-sm max-w-none">
            <ReactMarkdown>{result}</ReactMarkdown>
          </div>
        )}
      </div>

      {/* Refinement Section */}
      <div className="mt-8 bg-gray-50 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          Refine Your Results
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Not quite what you're looking for? Tell us how to adjust the recommendations.
        </p>

        <div className="flex gap-3">
          <input
            type="text"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder='e.g., "Remote only", "Exclude crypto", "Focus on startups"'
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            disabled={isRefining}
            onKeyDown={(e) => e.key === 'Enter' && handleRefine()}
          />
          <button
            onClick={handleRefine}
            disabled={feedback.trim().length < 3 || isRefining}
            className="px-6 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRefining ? 'Refining...' : 'Refine'}
          </button>
        </div>

        {/* Quick refinement chips */}
        <div className="flex flex-wrap gap-2 mt-4">
          {['Remote only', 'Hybrid in NYC', 'Exclude crypto', 'Focus on startups', 'Higher compensation'].map((chip) => (
            <button
              key={chip}
              onClick={() => setFeedback(chip)}
              className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-full hover:border-primary-500 hover:text-primary-600 transition-colors"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
