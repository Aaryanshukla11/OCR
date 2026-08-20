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
              className="bg-zinc-800 text-zinc-100 font-semibold px-0.5 rounded border border-zinc-600"
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
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 shadow-xs flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-zinc-800">
        <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center space-x-2 font-mono">
          <FileSearch className="w-4 h-4 text-zinc-400" />
          <span>Find in Image Text</span>
        </h3>
        {totalMatches > 0 && searchQuery.trim() && (
          <span className="text-[10px] bg-zinc-900 text-zinc-300 border border-zinc-800 px-2 py-0.5 rounded font-mono font-medium">
            {activeMatchIndex + 1} of {totalMatches} match{totalMatches > 1 ? 'es' : ''}
          </span>
        )}
      </div>

      {/* Search Input Controls Bar */}
      <div className="space-y-2 mb-3">
        <div className="relative flex items-center">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search text in document..."
            className="w-full pl-9 pr-24 py-1.5 bg-zinc-950 border border-zinc-800 rounded-md text-xs font-mono text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 transition-colors"
          />

          {/* Action buttons embedded in input */}
          <div className="absolute right-2 flex items-center space-x-1">
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="p-1 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 rounded transition-colors"
                title="Clear Search (Esc)"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}

            <button
              onClick={() => setIsMatchCase(!isMatchCase)}
              className={`p-1 rounded text-xs font-bold font-mono transition-colors ${
                isMatchCase
                  ? 'bg-zinc-800 text-zinc-100 border border-zinc-700'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800'
              }`}
              title={isMatchCase ? 'Match Case: ON' : 'Match Case: OFF'}
            >
              <CaseSensitive className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Match Navigation Bar */}
        {searchQuery.trim() && (
          <div className="flex items-center justify-between bg-zinc-950 px-3 py-1.5 rounded-md border border-zinc-800 text-xs">
            <span className="text-[11px] font-mono text-zinc-400">
              {totalMatches === 0 ? (
                <span className="text-rose-400">No matches found</span>
              ) : (
                <span>
                  Match <strong className="text-zinc-200">{activeMatchIndex + 1}</strong> of{' '}
                  <strong className="text-zinc-200">{totalMatches}</strong>
                </span>
              )}
            </span>

            <div className="flex items-center space-x-1">
              <button
                disabled={totalMatches === 0}
                onClick={handlePrevMatch}
                className="p-1 bg-zinc-900 hover:bg-zinc-800 disabled:opacity-30 text-zinc-300 rounded border border-zinc-800 transition-colors"
                title="Previous Match (Shift+Enter)"
              >
                <ChevronUp className="w-3.5 h-3.5" />
              </button>
              <button
                disabled={totalMatches === 0}
                onClick={handleNextMatch}
                className="p-1 bg-zinc-900 hover:bg-zinc-800 disabled:opacity-30 text-zinc-300 rounded border border-zinc-800 transition-colors"
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
          <div className="text-center py-8 text-xs text-zinc-500 font-mono">
            No document loaded. Run OCR to enable search.
          </div>
        ) : !searchQuery.trim() ? (
          <div className="text-center py-8 text-xs text-zinc-500 font-mono">
            Type text above to search inside the document image.
          </div>
        ) : totalMatches === 0 ? (
          <div className="text-center py-8 text-xs text-zinc-500 font-mono">
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
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  isActive
                    ? 'bg-zinc-800 border-zinc-600 text-zinc-100'
                    : isSelectedRegion
                    ? 'bg-zinc-900 border-zinc-700'
                    : 'bg-zinc-950/60 border-zinc-800/80 hover:border-zinc-700 hover:bg-zinc-900/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="w-5 h-5 rounded bg-zinc-900 border border-zinc-800 flex items-center justify-center text-[10px] font-mono font-medium text-zinc-300">
                      #{item.region.id}
                    </span>
                    {(data.pages?.length || 1) > 1 && (
                      <span className="text-[10px] text-zinc-400 font-mono bg-zinc-900 px-1.5 py-0.5 rounded border border-zinc-800">
                        Page {item.pageIndex + 1}
                      </span>
                    )}
                  </div>

                  <span className="text-[10px] font-mono text-zinc-400 flex items-center space-x-1">
                    <Target className="w-3 h-3 text-zinc-500" />
                    <span>{confPct}% conf</span>
                  </span>
                </div>

                <p className="text-xs text-zinc-200 font-mono bg-zinc-900/80 p-2 rounded border border-zinc-800 break-words leading-relaxed">
                  {renderHighlightedText(item.region.text, searchQuery, isMatchCase)}
                </p>

                {item.region.bbox && (
                  <div className="mt-1.5 flex items-center justify-between text-[10px] text-zinc-500 font-mono">
                    <span>
                      [{Math.round(item.region.bbox[0])}, {Math.round(item.region.bbox[1])}, {Math.round(item.region.bbox[2])}, {Math.round(item.region.bbox[3])}]
                    </span>
                    {isActive && (
                      <span className="text-zinc-300 font-medium uppercase tracking-wider text-[9px]">
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

