import React from 'react';
import { Award, CheckCircle2, HelpCircle } from 'lucide-react';
import type { AccuracyMetrics } from '../types';

interface AccuracyEvalPanelProps {
  accuracy: AccuracyMetrics;
}

export const AccuracyEvalPanel: React.FC<AccuracyEvalPanelProps> = ({ accuracy }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center space-x-2">
        <Award className="w-4 h-4 text-purple-400" />
        <span>Accuracy Measurement</span>
      </h3>

      {accuracy.available ? (
        <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 space-y-3">
          <div className="flex items-center space-x-2 text-xs text-emerald-400 font-semibold">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Ground Truth Evaluation Complete</span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-slate-900 p-3 rounded border border-slate-800">
              <span className="text-[11px] text-slate-400 font-mono block mb-1">Character Error Rate (CER)</span>
              <span className="text-xl font-bold font-mono text-emerald-400">{accuracy.cer}%</span>
              <p className="text-[10px] text-slate-500 mt-1">Lower is better (Levenshtein distance per character)</p>
            </div>

            <div className="bg-slate-900 p-3 rounded border border-slate-800">
              <span className="text-[11px] text-slate-400 font-mono block mb-1">Word Error Rate (WER)</span>
              <span className="text-xl font-bold font-mono text-cyan-400">{accuracy.wer}%</span>
              <p className="text-[10px] text-slate-500 mt-1">Lower is better (Levenshtein distance per word token)</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-950 p-4 rounded-lg border border-slate-800/80 flex items-center space-x-3">
          <div className="w-8 h-8 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 flex-shrink-0">
            <HelpCircle className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-300">Accuracy Score Status</p>
            <p className="text-xs text-amber-400/90 font-mono mt-0.5">{accuracy.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};
