/**
 * ResumeUpload Component - File upload and text paste
 */

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

interface ResumeUploadProps {
  onFileUpload: (file: File) => void;
  onTextSubmit: (text: string) => void;
  isLoading: boolean;
}

export function ResumeUpload({ onFileUpload, onTextSubmit, isLoading }: ResumeUploadProps) {
  const [mode, setMode] = useState<'upload' | 'paste'>('upload');
  const [pastedText, setPastedText] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0]);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: isLoading,
  });

  const handleTextSubmit = () => {
    if (pastedText.trim().length >= 100) {
      onTextSubmit(pastedText.trim());
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Mode Toggle */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setMode('upload')}
          className={`px-6 py-3 font-medium text-sm transition-colors ${
            mode === 'upload'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Upload File
        </button>
        <button
          onClick={() => setMode('paste')}
          className={`px-6 py-3 font-medium text-sm transition-colors ${
            mode === 'paste'
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Paste Text
        </button>
      </div>

      {mode === 'upload' ? (
        /* File Upload */
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
            ${isDragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }
            ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />

          <div className="mb-4">
            <svg className="w-12 h-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>

          {isDragActive ? (
            <p className="text-primary-600 font-medium">Drop your resume here...</p>
          ) : (
            <>
              <p className="text-gray-700 font-medium mb-1">
                Drag and drop your resume here
              </p>
              <p className="text-gray-500 text-sm mb-4">
                or click to select a file
              </p>
              <p className="text-gray-400 text-xs">
                PDF, DOCX, TXT, or MD — up to 10MB
              </p>
              <p className="text-gray-400 text-xs mt-3 flex items-center justify-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                Your resume is not stored
              </p>
            </>
          )}
        </div>
      ) : (
        /* Text Paste */
        <div className="space-y-4">
          <textarea
            value={pastedText}
            onChange={(e) => setPastedText(e.target.value)}
            placeholder="Paste your resume text here..."
            className="w-full h-64 p-4 border border-gray-300 rounded-xl resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-shadow"
            disabled={isLoading}
          />

          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">
              {pastedText.length} characters (minimum 100)
            </span>
            <button
              onClick={handleTextSubmit}
              disabled={pastedText.trim().length < 100 || isLoading}
              className="px-6 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Analyze Resume
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
