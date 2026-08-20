import React, { useEffect, useRef } from 'react';
import { Search, X, ChevronUp, ChevronDown, CaseSensitive, Target, FileSearch } from 'lucide-react';
import type { OCRResponse, BoundingBoxRegion } from '../types';

export interface SearchMatchItem {
  pageIndex: number;
  region: BoundingBoxRegion;
}

interface FindTextPanelProps {
  data: OCRResponse | null;
  activePageIndex: number;
  setActivePageIndex: (pageIdx: number) => void;
  selectedRegionId: number | null;
  setSelectedRegionId: (id: number | null) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  isMatchCase: boolean;
  setIsMatchCase: (val: boolean) => void;
  activeMatchIndex: number;
  setActiveMatchIndex: React.Dispatch<React.SetStateAction<number>>;
  matchingRegions: SearchMatchItem[];
}

export const FindTextPanel: React.FC<FindTextPanelProps> = ({
  data,
  setActivePageIndex,
  selectedRegionId,
  setSelectedRegionId,
  searchQuery,
  setSearchQuery,
  isMatchCase,
  setIsMatchCase,
  activeMatchIndex,
  setActiveMatchIndex,
  matchingRegions,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const matchItemRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  const totalMatches = matchingRegions.length;

  // Auto-focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Scroll active match item into view in search list
  useEffect(() => {
    if (totalMatches > 0 && activeMatchIndex >= 0 && activeMatchIndex < totalMatches) {
      const activeMatch = matchingRegions[activeMatchIndex];
      if (activeMatch) {
        const key = `${activeMatch.pageIndex}-${activeMatch.region.id}`;
        matchItemRefs.current[key]?.scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
        });
      }
    }
  }, [activeMatchIndex, matchingRegions, totalMatches]);

  const handleNextMatch = () => {
    if (totalMatches === 0) return;
    const nextIdx = (activeMatchIndex + 1) % totalMatches;
    setActiveMatchIndex(nextIdx);
    const match = matchingRegions[nextIdx];
    if (match) {
      setActivePageIndex(match.pageIndex);
      setSelectedRegionId(match.region.id);
    }
  };

  const handlePrevMatch = () => {
    if (totalMatches === 0) return;
    const prevIdx = (activeMatchIndex - 1 + totalMatches) % totalMatches;
    setActiveMatchIndex(prevIdx);
    const match = matchingRegions[prevIdx];
    if (match) {
      setActivePageIndex(match.pageIndex);
      setSelectedRegionId(match.region.id);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (e.shiftKey) {
        handlePrevMatch();
      } else {
        handleNextMatch();
      }
    } else if (e.key === 'Escape') {
      setSearchQuery('');
    }
  };

  const handleSelectMatch = (index: number) => {
    setActiveMatchIndex(index);
    const match = matchingRegions[index];
    if (match) {
      setActivePageIndex(match.pageIndex);
      setSelectedRegionId(match.region.id);
    }
  };

  // Helper to render text with highlighted matching substring
  const renderHighlightedText = (text: string, query: string, matchCase: boolean) => {
    if (!query.trim()) return text;
    const flags = matchCase ? 'g' : 'gi';
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, flags);
    const parts = text.split(regex);

    return (
      <>
        {parts.map((part, i) =>
          regex.test(part) ? (
            <mark
              key={i}
              className="bg-amber-400/30 text-amber-200 font-bold px-0.5 rounded border border-amber-400/50 shadow-sm"
            >
              {part}
            </mark>
          ) : (
            <span key={i}>{part}</span>
          )
        )}
      </>
    );
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
          <FileSearch className="w-4 h-4 text-amber-400" />
          <span>Find in Image Text</span>
        </h3>
        {totalMatches > 0 && searchQuery.trim() && (
          <span className="text-[10px] bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded font-mono font-semibold">
            {activeMatchIndex + 1} of {totalMatches} match{totalMatches > 1 ? 'es' : ''}
          </span>
        )}
      </div>

      {/* Search Input Controls Bar */}
      <div className="space-y-2 mb-3">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search text in document/image..."
            className="w-full pl-9 pr-24 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500/40 transition-all"
          />

          {/* Action buttons embedded in input */}
          <div className="absolute right-2 flex items-center space-x-1">
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition-colors"
                title="Clear Search (Esc)"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              onClick={() => setIsMatchCase(!isMatchCase)}
              className={`p-1 rounded text-xs font-bold font-mono transition-colors ${
                isMatchCase
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
              title={isMatchCase ? 'Match Case: ON' : 'Match Case: OFF'}
            >
              <CaseSensitive className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Match Navigation Bar */}
        {searchQuery.trim() && (
          <div className="flex items-center justify-between bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <span className="text-[11px] font-mono text-slate-400">
              {totalMatches === 0 ? (
                <span className="text-rose-400 font-semibold">No matches found</span>
              ) : (
                <span>
                  Match <strong className="text-amber-400">{activeMatchIndex + 1}</strong> of{' '}
                  <strong className="text-amber-400">{totalMatches}</strong>
                </span>
              )}
            </span>

            <div className="flex items-center space-x-1">
              <button
                disabled={totalMatches === 0}
                onClick={handlePrevMatch}
                className="p-1 bg-slate-900 hover:bg-slate-800 disabled:opacity-30 text-slate-300 rounded border border-slate-800 transition-colors"
                title="Previous Match (Shift+Enter)"
              >
                <ChevronUp className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={totalMatches === 0}
                onClick={handleNextMatch}
                className="p-1 bg-slate-900 hover:bg-slate-800 disabled:opacity-30 text-slate-300 rounded border border-slate-800 transition-colors"
                title="Next Match (Enter)"
              >
                <ChevronDown className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Results List */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[420px]">
        {!data ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No document loaded. Run OCR to enable search.
          </div>
        ) : !searchQuery.trim() ? (
          <div className="text-center py-8 text-xs text-slate-500 font-mono">
            Type text above to search inside the document image.
          </div>
        ) : totalMatches === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No region containing "{searchQuery}" was found.
          </div>
        ) : (
          matchingRegions.map((item, index) => {
            const isActive = index === activeMatchIndex;
            const isSelectedRegion = selectedRegionId === item.region.id;
            const key = `${item.pageIndex}-${item.region.id}`;
            const confPct = Math.round(item.region.confidence * 100);

            return (
              <div
                key={key}
                ref={(el) => {
                  matchItemRefs.current[key] = el;
                }}
                onClick={() => handleSelectMatch(index)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  isActive
                    ? 'bg-amber-950/40 border-amber-500/70 shadow-lg shadow-amber-500/10 ring-1 ring-amber-500/30'
                    : isSelectedRegion
                    ? 'bg-slate-900 border-indigo-500/50'
                    : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 hover:bg-slate-950'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="w-5 h-5 rounded bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-[10px] font-mono font-bold text-amber-300">
                      #{item.region.id}
                    </span>
                    {(data.pages?.length || 1) > 1 && (
                      <span className="text-[10px] text-slate-400 font-mono bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                        Page {item.pageIndex + 1}
                      </span>
                    )}
                  </div>

                  <span className="text-[10px] font-mono text-slate-400 flex items-center space-x-1">
                    <Target className="w-3 h-3 text-slate-500" />
                    <span>{confPct}% conf</span>
                  </span>
                </div>

                <p className="text-xs text-slate-200 font-mono bg-slate-900/80 p-2 rounded border border-slate-800/90 break-words leading-relaxed">
                  {renderHighlightedText(item.region.text, searchQuery, isMatchCase)}
                </p>

                {item.region.bbox && (
                  <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                    <span>
                      BBox: [{Math.round(item.region.bbox[0])}, {Math.round(item.region.bbox[1])}, {Math.round(item.region.bbox[2])}, {Math.round(item.region.bbox[3])}]
                    </span>
                    {isActive && (
                      <span className="text-amber-400 font-semibold uppercase tracking-wider text-[9px]">
                        Active Match
                      </span>
                    )}
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
