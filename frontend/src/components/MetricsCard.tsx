import React from 'react';
import { Cpu, Zap, Clock, Target, Award, Layers } from 'lucide-react';
import type { OCRResponse } from '../types';

interface MetricsCardProps {
  data: OCRResponse;
}

export const MetricsCard: React.FC<MetricsCardProps> = ({ data }) => {
  const isGpu = data.device.toUpperCase().includes('GPU');
  
  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 shadow-xs">
      <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3 flex items-center justify-between font-mono">
        <span className="flex items-center space-x-2">
          <Target className="w-4 h-4 text-zinc-400" />
          <span>Execution & Evaluation Metrics</span>
        </span>
        <span className="text-[10px] bg-zinc-900 text-zinc-400 px-2 py-0.5 rounded border border-zinc-800">
          Runtime Data
        </span>
      </h3>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {/* Model */}
        <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
          <div className="flex items-center text-[10px] text-zinc-500 mb-1 space-x-1 font-mono">
            <Layers className="w-3 h-3 text-zinc-400" />
            <span>MODEL</span>
          </div>
          <p className="text-xs font-semibold text-zinc-100 font-mono">PaddleOCR 3.7.0</p>
        </div>

        {/* Device */}
        <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
          <div className="flex items-center text-[10px] text-zinc-500 mb-1 space-x-1 font-mono">
            {isGpu ? <Zap className="w-3 h-3 text-zinc-300" /> : <Cpu className="w-3 h-3 text-zinc-400" />}
            <span>DEVICE</span>
          </div>
          <p className="text-xs font-semibold text-zinc-100 font-mono">
            {data.device}
          </p>
        </div>

        {/* Processing Time */}
        <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
          <div className="flex items-center text-[10px] text-zinc-500 mb-1 space-x-1 font-mono">
            <Clock className="w-3 h-3 text-zinc-400" />
            <span>LATENCY</span>
          </div>
          <p className="text-xs font-semibold text-zinc-100 font-mono">{data.processing_time}s</p>
        </div>

        {/* Detected Regions */}
        <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
          <div className="flex items-center text-[10px] text-zinc-500 mb-1 space-x-1 font-mono">
            <Target className="w-3 h-3 text-zinc-400" />
            <span>REGIONS</span>
          </div>
          <p className="text-xs font-semibold text-zinc-100 font-mono">{data.total_regions} detected</p>
        </div>

        {/* Avg Confidence */}
        <div className="bg-zinc-950 p-3 rounded-lg border border-zinc-800">
          <div className="flex items-center text-[10px] text-zinc-500 mb-1 space-x-1 font-mono">
            <Award className="w-3 h-3 text-zinc-400" />
            <span>AVG CONFIDENCE</span>
          </div>
          <p className="text-xs font-semibold text-zinc-100 font-mono">{data.average_confidence}%</p>
        </div>
      </div>

      {/* Accuracy Evaluation Banner */}
      <div className="mt-3 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs">
        <span className="text-zinc-400 font-medium text-xs">Ground Truth Evaluation:</span>
        {data.accuracy.available ? (
          <div className="flex items-center space-x-2 font-mono text-xs">
            <span className="bg-zinc-900 text-zinc-200 px-2 py-0.5 rounded border border-zinc-800">
              CER: {data.accuracy.cer}%
            </span>
            <span className="bg-zinc-900 text-zinc-200 px-2 py-0.5 rounded border border-zinc-800">
              WER: {data.accuracy.wer}%
            </span>
          </div>
        ) : (
          <span className="text-zinc-400 font-mono text-[11px] bg-zinc-950 px-2 py-0.5 rounded border border-zinc-800">
            {data.accuracy.message}
          </span>
        )}
      </div>
    </div>
  );
};

