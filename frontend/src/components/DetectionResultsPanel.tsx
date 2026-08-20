import React, { useEffect, useRef } from 'react';
import { Target } from 'lucide-react';
import type { PageOCRResult } from '../types';

interface DetectionResultsPanelProps {
  pageResult: PageOCRResult;
  selectedRegionId: number | null;
  setSelectedRegionId: (id: number | null) => void;
}

export const DetectionResultsPanel: React.FC<DetectionResultsPanelProps> = ({
  pageResult,
  selectedRegionId,
  setSelectedRegionId,
}) => {
  const regions = pageResult?.regions || [];
  const itemRefs = useRef<{ [key: number]: HTMLDivElement | null }>({});

  useEffect(() => {
    if (selectedRegionId !== null && itemRefs.current[selectedRegionId]) {
      itemRefs.current[selectedRegionId]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      });
    }
  }, [selectedRegionId]);

  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 shadow-xs flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800">
        <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center space-x-2 font-mono">
          <Target className="w-4 h-4 text-zinc-400" />
          <span>Detection Regions ({regions.length})</span>
        </h3>
        <span className="text-[10px] text-zinc-500 font-mono">
          Page {pageResult?.page_number || 1}
        </span>
      </div>

      {/* Regions List */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[500px]">
        {regions.length === 0 ? (
          <div className="text-center py-8 text-xs text-zinc-500 font-mono">
            No bounding box regions detected.
          </div>
        ) : (
          regions.map((region) => {
            const isSelected = selectedRegionId === region.id;
            const confPct = Math.round(region.confidence * 100);

            return (
              <div
                key={region.id}
                ref={(el) => {
                  itemRefs.current[region.id] = el;
                }}
                onClick={() => setSelectedRegionId(region.id)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-zinc-800 border-zinc-600 text-zinc-100'
                    : 'bg-zinc-950/60 border-zinc-800/80 hover:border-zinc-700 hover:bg-zinc-900/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-mono font-semibold text-zinc-400 flex items-center space-x-1">
                    <span className="w-5 h-5 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-[10px] text-zinc-300">
                      {String(region.id).padStart(2, '0')}
                    </span>
                  </span>

                  <span className="text-[10px] px-2 py-0.5 rounded font-mono border border-zinc-800 bg-zinc-900 text-zinc-300">
                    Conf: {confPct}%
                  </span>
                </div>

                <p className="text-xs text-zinc-200 font-mono bg-zinc-900/80 p-2 rounded border border-zinc-800 break-words">
                  {region.text}
                </p>

                {region.bbox && (
                  <div className="mt-1.5 flex items-center justify-between text-[10px] text-zinc-500 font-mono">
                    <span>
                      [{Math.round(region.bbox[0])}, {Math.round(region.bbox[1])}, {Math.round(region.bbox[2])}, {Math.round(region.bbox[3])}]
                    </span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

