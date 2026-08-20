import React, { useState } from 'react';
import { Copy, Download, FileText, Check, Code } from 'lucide-react';
import type { OCRResponse } from '../types';

interface ExtractedTextPanelProps {
  data: OCRResponse;
}

export const ExtractedTextPanel: React.FC<ExtractedTextPanelProps> = ({ data }) => {
  const [copied, setCopied] = useState(false);

  const textToCopy = data.aggregated_text;

  const handleCopy = () => {
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadTxt = () => {
    const blob = new Blob([textToCopy], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.filename.split('.')[0]}_extracted.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.filename.split('.')[0]}_ocr_results.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full">
      {/* Header with Export Controls */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <span>Extracted Text</span>
        </h3>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center space-x-1 transition-colors"
            title="Copy extracted text to clipboard"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>

          <button
            onClick={handleDownloadTxt}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center space-x-1 transition-colors"
            title="Download extracted text as .TXT"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>TXT</span>
          </button>

          <button
            onClick={handleDownloadJson}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 flex items-center space-x-1 transition-colors"
            title="Download full result structure as .JSON"
          >
            <Code className="w-3.5 h-3.5 text-cyan-400" />
            <span>JSON</span>
          </button>
        </div>
      </div>

      <div className="flex-1 bg-slate-950 rounded-lg border border-slate-800/80 p-4 font-mono text-xs text-slate-200 leading-relaxed overflow-y-auto whitespace-pre-wrap select-text selection:bg-indigo-500 selection:text-white min-h-[220px]">
        {data.aggregated_text || <span className="text-slate-600 italic">No text recognized in this document.</span>}
      </div>
    </div>
  );
};
