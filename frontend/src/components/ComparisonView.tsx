import React from 'react';
import { Columns, FileImage, FileText } from 'lucide-react';
import type { OCRResponse } from '../types';

interface ComparisonViewProps {
  imageSrc: string;
  data: OCRResponse;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({ imageSrc, data }) => {
  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 shadow-xs">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-zinc-800">
        <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center space-x-2 font-mono">
          <Columns className="w-4 h-4 text-zinc-400" />
          <span>Visual Comparison Mode</span>
        </h3>
        <span className="text-xs text-zinc-400 font-mono">
          Evaluating Alignment
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Panel 1: Original Document */}
        <div className="bg-zinc-950 p-4 rounded-lg border border-zinc-800 flex flex-col">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-800 text-xs font-mono">
            <span className="font-medium text-zinc-300 flex items-center space-x-1.5">
              <FileImage className="w-3.5 h-3.5 text-zinc-400" />
              <span>ORIGINAL DOCUMENT</span>
            </span>
            <span className="text-zinc-500">{data.filename}</span>
          </div>

          <div className="flex-1 min-h-[300px] flex items-center justify-center bg-zinc-900/40 rounded p-2 overflow-hidden">
            <img
              src={imageSrc}
              alt="Original Document"
              className="max-w-full max-h-[450px] object-contain rounded border border-zinc-800"
            />
          </div>
        </div>

        {/* Panel 2: OCR Extracted Text & Ground Truth */}
        <div className="bg-zinc-950 p-4 rounded-lg border border-zinc-800 flex flex-col">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-zinc-800 text-xs font-mono">
            <span className="font-medium text-zinc-300 flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-zinc-400" />
              <span>OCR EXTRACTED OUTPUT</span>
            </span>
            <span className="text-zinc-300 font-medium">
              Conf: {data.average_confidence}%
            </span>
          </div>

          {/* Extracted Text */}
          <div className="flex-1 bg-zinc-900 rounded p-4 font-mono text-xs text-zinc-300 leading-relaxed overflow-y-auto max-h-[350px] whitespace-pre-wrap border border-zinc-800 select-text">
            {data.aggregated_text}
          </div>

          {/* Ground Truth Comparison Summary if available */}
          {data.accuracy.available && (
            <div className="mt-4 p-3 bg-zinc-900 border border-zinc-800 rounded-md text-xs">
              <div className="flex items-center justify-between mb-1 text-zinc-300 font-medium font-mono">
                <span>Ground Truth Reference</span>
                <span>CER: {data.accuracy.cer}% | WER: {data.accuracy.wer}%</span>
              </div>
              <div className="font-mono text-[11px] text-zinc-400 bg-zinc-950 p-2 rounded max-h-24 overflow-y-auto whitespace-pre-wrap border border-zinc-800">
                {data.accuracy.ground_truth}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

