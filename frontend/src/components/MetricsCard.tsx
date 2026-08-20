import React from 'react';
import { Cpu, Zap, Clock, Target, Award, Layers } from 'lucide-react';
import type { OCRResponse } from '../types';

interface MetricsCardProps {
  data: OCRResponse;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({ data }) => {
  const isGpu = data.device.toUpperCase().includes('GPU');
  
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center justify-between">
        <span className="flex items-center space-x-2">
          <Target className="w-4 h-4 text-indigo-400" />
          <span>Execution & Evaluation Metrics</span>
        </span>
        <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-mono">
          Actual Runtime Data
        </span>
      </h3>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {/* Model */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
          <div className="flex items-center text-xs text-slate-400 mb-1 space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>MODEL</span>
          </div>
          <p className="text-sm font-bold text-white tracking-tight">PaddleOCR 3.7.0</p>
        </div>

        {/* Device */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
          <div className="flex items-center text-xs text-slate-400 mb-1 space-x-1.5">
            {isGpu ? <Zap className="w-3.5 h-3.5 text-amber-400" /> : <Cpu className="w-3.5 h-3.5 text-blue-400" />}
            <span>DEVICE</span>
          </div>
          <p className={`text-sm font-bold tracking-tight ${isGpu ? 'text-amber-300' : 'text-slate-200'}`}>
            {data.device}
          </p>
        </div>

        {/* Processing Time */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
          <div className="flex items-center text-xs text-slate-400 mb-1 space-x-1.5">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            <span>LATENCY</span>
          </div>
          <p className="text-sm font-bold text-emerald-400 font-mono">{data.processing_time} sec</p>
        </div>

        {/* Detected Regions */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
          <div className="flex items-center text-xs text-slate-400 mb-1 space-x-1.5">
            <Target className="w-3.5 h-3.5 text-cyan-400" />
            <span>REGIONS</span>
          </div>
          <p className="text-sm font-bold text-cyan-300 font-mono">{data.total_regions} detected</p>
        </div>

        {/* Avg Confidence */}
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
          <div className="flex items-center text-xs text-slate-400 mb-1 space-x-1.5">
            <Award className="w-3.5 h-3.5 text-purple-400" />
            <span>AVG CONFIDENCE</span>
          </div>
          <p className="text-sm font-bold text-purple-300 font-mono">{data.average_confidence}%</p>
        </div>
      </div>

      {/* Accuracy Evaluation Banner */}
      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
        <span className="text-slate-400 font-medium">Ground Truth Accuracy Evaluation:</span>
        {data.accuracy.available ? (
          <div className="flex items-center space-x-3 font-mono">
            <span className="bg-emerald-500/10 text-emerald-300 px-2 py-0.5 rounded border border-emerald-500/20">
              CER: {data.accuracy.cer}%
            </span>
            <span className="bg-cyan-500/10 text-cyan-300 px-2 py-0.5 rounded border border-cyan-500/20">
              WER: {data.accuracy.wer}%
            </span>
          </div>
        ) : (
          <span className="text-amber-400/90 font-mono text-[11px] bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
            {data.accuracy.message}
          </span>
        )}
      </div>
    </div>
  );
};
