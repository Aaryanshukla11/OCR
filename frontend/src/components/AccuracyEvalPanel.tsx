import React from 'react';
import { Award, CheckCircle2, HelpCircle } from 'lucide-react';
import type { AccuracyMetrics } from '../types';

interface AccuracyEvalPanelProps {
  accuracy: AccuracyMetrics;
}

export const AccuracyEvalPanel: React.FC<AccuracyEvalPanelProps> = ({ accuracy }) => {
  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 shadow-xs">
      <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3 flex items-center space-x-2 font-mono">
        <Award className="w-4 h-4 text-zinc-400" />
        <span>Accuracy Measurement</span>
      </h3>

      {accuracy.available ? (
        <div className="bg-zinc-950 p-4 rounded-lg border border-zinc-800 space-y-3 font-mono">
          <div className="flex items-center space-x-2 text-xs text-emerald-400 font-medium">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Ground Truth Evaluation Complete</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="bg-zinc-900 p-3 rounded border border-zinc-800">
              <span className="text-[11px] text-zinc-400 block mb-1">Character Error Rate (CER)</span>
              <span className="text-xl font-semibold text-zinc-100">{accuracy.cer}%</span>
              <p className="text-[10px] text-zinc-500 mt-1">Lower is better</p>
            </div>

            <div className="bg-zinc-900 p-3 rounded border border-zinc-800">
              <span className="text-[11px] text-zinc-400 block mb-1">Word Error Rate (WER)</span>
              <span className="text-xl font-semibold text-zinc-100">{accuracy.wer}%</span>
              <p className="text-[10px] text-zinc-500 mt-1">Lower is better</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-zinc-950 p-4 rounded-lg border border-zinc-800 flex items-center space-x-3">
          <div className="w-7 h-7 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 flex-shrink-0">
            <HelpCircle className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-medium text-zinc-300 font-mono">Accuracy Score Status</p>
            <p className="text-xs text-zinc-400 font-mono mt-0.5">{accuracy.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};

