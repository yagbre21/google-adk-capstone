/**
 * ExampleModal Component - Shows sample results to demonstrate value
 */

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface ExampleModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Sample results based on a Senior Textile Designer resume
const SAMPLE_RESULT = `## RESUME ANALYSIS

**Current Role:** Senior Textile Designer at Macy's Private Brands (15.8 YOE total, 2.6 years avg tenure)

**Estimated Market Compensation:** $130,000 - $170,000 (what they could command on the open market based on skills/experience, NOT current salary)

**Profession:** Fashion/Textile Design

**Key Skills:** NedGraphics Pro, Kaledo, Adobe Photoshop CC, Adobe Illustrator CC, Adobe InDesign CC

**Career Trajectory:** Associate CAD Designer → CAD Designer → Senior CAD Designer → Senior Textile Designer

**Inferred Direction:** Likely aiming for Design Director or Creative Director roles in fashion or textiles, potentially with a focus on private label brands.

## LEVEL CLASSIFICATION RESULT

**Final Level:** L6 (Lead Designer/Design Director)

**Confidence:** Medium

**Agreement:** 2/3 agents

**VOTE BREAKDOWN:**

- Conservative Evaluator: L5 (Senior) - "Strong technical skills but limited leadership evidence"
- Optimistic Evaluator: L6 (Lead) - "15+ years experience with progressive responsibility"
- Tie Breaker: L6 (Lead) - "Scope of work at Macy's suggests director-level impact"

## EXACT MATCH: Design Director, Private Label

**Company:** Target Corporation

**Location:** Minneapolis, MN (Hybrid)

**Compensation:** $145,000 - $175,000 + bonus

**Why This Fits:** Direct alignment with private label experience at Macy's. Your textile expertise and CAD proficiency match their technical requirements. Similar scale retail environment.

[View Job Posting](https://example.com/job1)

## LEVEL UP: Creative Director, Apparel

**Company:** Everlane

**Location:** San Francisco, CA (Remote-friendly)

**Compensation:** $180,000 - $220,000 + equity

**Why This Fits:** Step up to creative leadership. Your trajectory from CAD to Senior Designer shows growth. Everlane's sustainable focus aligns with modern textile practices.

[View Job Posting](https://example.com/job2)

## STRETCH: VP of Design

**Company:** Reformation

**Location:** Los Angeles, CA

**Compensation:** $250,000 - $300,000 + equity

**Why This Fits:** Ambitious but achievable. Your 15+ years and private label experience provide foundation. Would need to demonstrate team leadership and P&L ownership.

[View Job Posting](https://example.com/job3)

## TRAJECTORY: Head of Sustainable Textiles

**Company:** Patagonia

**Location:** Ventura, CA

**Compensation:** $200,000 - $240,000

**Why This Fits:** Future-oriented role combining your textile expertise with growing sustainability focus. Represents where the industry is heading. Your technical depth in fabric design is highly relevant.

[View Job Posting](https://example.com/job4)`;

// Section styling (matches ResultDisplay)
const getSectionStyle = (title: string) => {
  if (title.includes('RESUME ANALYSIS')) {
    return 'bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-500';
  }
  if (title.includes('LEVEL CLASSIFICATION')) {
    return 'bg-gradient-to-r from-purple-50 to-violet-50 border-l-4 border-purple-500';
  }
  if (title.includes('EXACT MATCH')) {
    return 'bg-gradient-to-r from-emerald-50 to-green-50 border-l-4 border-emerald-500';
  }
  if (title.includes('LEVEL UP')) {
    return 'bg-gradient-to-r from-orange-50 to-amber-50 border-l-4 border-orange-500';
  }
  if (title.includes('STRETCH')) {
    return 'bg-gradient-to-r from-red-50 to-rose-50 border-l-4 border-red-500';
  }
  if (title.includes('TRAJECTORY')) {
    return 'bg-gradient-to-r from-violet-50 to-purple-50 border-l-4 border-violet-500';
  }
  return 'bg-gray-50 border-l-4 border-gray-300';
};

// Parse into sections
const parseIntoSections = (markdown: string) => {
  const sections: { title: string; content: string }[] = [];
  const lines = markdown.split('\n');
  let currentSection: { title: string; content: string[] } | null = null;

  for (const line of lines) {
    if (line.startsWith('## ')) {
      if (currentSection) {
        sections.push({
          title: currentSection.title,
          content: currentSection.content.join('\n')
        });
      }
      currentSection = { title: line.substring(3), content: [] };
    } else if (currentSection) {
      currentSection.content.push(line);
    }
  }

  if (currentSection) {
    sections.push({
      title: currentSection.title,
      content: currentSection.content.join('\n')
    });
  }

  return sections;
};

export function ExampleModal({ isOpen, onClose }: ExampleModalProps) {
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0, 1])); // First two expanded by default

  if (!isOpen) return null;

  const sections = parseIntoSections(SAMPLE_RESULT);

  const toggleSection = (index: number) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative min-h-screen flex items-start justify-center p-4 pt-16">
        <div className="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Example Results</h2>
              <p className="text-sm text-gray-500">Based on a Senior Textile Designer resume</p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {sections.map((section, index) => {
              const isExpanded = expandedSections.has(index);
              const style = getSectionStyle(section.title);

              return (
                <div key={index}>
                  <button
                    onClick={() => toggleSection(index)}
                    className={`w-full text-left px-5 py-3 ${style} flex items-center justify-between hover:opacity-90 transition-opacity rounded-lg shadow-sm`}
                  >
                    <h3 className="text-lg font-bold text-gray-900">{section.title}</h3>
                    <svg
                      className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {isExpanded && (
                    <div className="px-5 py-4 prose prose-sm max-w-none">
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => (
                            <p className="text-gray-700 mb-3 leading-relaxed">{children}</p>
                          ),
                          strong: ({ children }) => (
                            <strong className="font-semibold text-gray-900">{children}</strong>
                          ),
                          ul: ({ children }) => (
                            <ul className="space-y-1 mb-3 ml-1">{children}</ul>
                          ),
                          li: ({ children }) => (
                            <li className="text-gray-700 flex items-start gap-2">
                              <span className="text-primary-500 mt-1.5 text-xs">-</span>
                              <span>{children}</span>
                            </li>
                          ),
                          a: ({ children }) => (
                            <span className="inline-flex items-center gap-1 text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded cursor-not-allowed opacity-60">
                              {children}
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </span>
                          ),
                        }}
                      >
                        {section.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            <p className="text-sm text-gray-500 text-center">
              This is sample output. Upload your resume to get personalized results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
