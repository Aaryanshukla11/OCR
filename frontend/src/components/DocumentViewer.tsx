import React, { useState, useRef } from 'react';
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Eye, EyeOff, ChevronLeft, ChevronRight, Layers, Search, X, ChevronUp, ChevronDown } from 'lucide-react';
import type { PageOCRResult } from '../types';

interface DocumentViewerProps {
  imageSrc: string;
  pageResults: PageOCRResult[];
  activePageIndex: number;
  setActivePageIndex: (idx: number) => void;
  selectedRegionId: number | null;
  setSelectedRegionId: (id: number | null) => void;
  searchQuery?: string;
  setSearchQuery?: (q: string) => void;
  matchingRegionIds?: Set<number>;
  activeMatchRegionId?: number | null;
  onNavigateNextMatch?: () => void;
  onNavigatePrevMatch?: () => void;
  totalMatchesCount?: number;
  currentMatchIndex?: number;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  imageSrc,
  pageResults,
  activePageIndex,
  setActivePageIndex,
  selectedRegionId,
  setSelectedRegionId,
  searchQuery = '',
  setSearchQuery,
  matchingRegionIds = new Set(),
  activeMatchRegionId = null,
  onNavigateNextMatch,
  onNavigatePrevMatch,
  totalMatchesCount = 0,
  currentMatchIndex = 0,
}) => {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [startPan, setStartPan] = useState({ x: 0, y: 0 });
  const [showBoxes, setShowBoxes] = useState(true);
  const [showInlineSearch, setShowInlineSearch] = useState(false);
  
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0, naturalWidth: 0, naturalHeight: 0 });

  const currentPage = pageResults[activePageIndex] || pageResults[0];
  const regions = currentPage?.regions || [];

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 4));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };
  
  const handleFitToScreen = () => {
    if (containerRef.current && imgRef.current) {
      const containerW = containerRef.current.clientWidth - 40;
      const imgW = imgRef.current.naturalWidth || 600;
      const fitZoom = containerW / imgW;
      setZoom(Math.min(Math.max(fitZoom, 0.5), 2));
      setPan({ x: 0, y: 0 });
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsPanning(true);
      setStartPan({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setPan({
        x: e.clientX - startPan.x,
        y: e.clientY - startPan.y,
      });
    }
  };

  const handleMouseUp = () => setIsPanning(false);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImageDimensions({
      width: img.clientWidth,
      height: img.clientHeight,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
    });
  };

  const hasSearch = searchQuery.trim().length > 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl flex flex-col h-full">
      {/* Control Bar */}
      <div className="bg-slate-950 px-4 py-2.5 border-b border-slate-800 flex flex-wrap items-center justify-between text-xs select-none gap-2">
        
        {/* Title & Page Nav */}
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-slate-300 flex items-center space-x-1">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>Document Viewer</span>
          </span>

          {pageResults.length > 1 && (
            <div className="flex items-center space-x-1.5 bg-slate-900 px-2 py-1 rounded border border-slate-800">
              <button
                disabled={activePageIndex === 0}
                onClick={() => setActivePageIndex(activePageIndex - 1)}
                className="p-0.5 text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-slate-300 font-mono">
                Page {activePageIndex + 1} of {pageResults.length}
              </span>
              <button
                disabled={activePageIndex === pageResults.length - 1}
                onClick={() => setActivePageIndex(activePageIndex + 1)}
                className="p-0.5 text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Search Bar / Find Controls */}
        <div className="flex items-center space-x-2">
          {showInlineSearch && setSearchQuery ? (
            <div className="flex items-center space-x-1 bg-slate-900 px-2 py-1 rounded-lg border border-amber-500/40">
              <Search className="w-3.5 h-3.5 text-amber-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Find in image..."
                className="bg-transparent text-xs text-slate-100 placeholder-slate-500 focus:outline-none w-32 sm:w-44 font-mono"
                autoFocus
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="text-slate-400 hover:text-white p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
              {totalMatchesCount > 0 && (
                <div className="flex items-center space-x-1 pl-1 border-l border-slate-800 text-[10px] font-mono text-amber-300">
                  <span>{currentMatchIndex + 1}/{totalMatchesCount}</span>
                  <button
                    onClick={onNavigatePrevMatch}
                    className="hover:text-white p-0.5"
                    title="Previous match"
                  >
                    <ChevronUp className="w-3 h-3" />
                  </button>
                  <button
                    onClick={onNavigateNextMatch}
                    className="hover:text-white p-0.5"
                    title="Next match"
                  >
                    <ChevronDown className="w-3 h-3" />
                  </button>
                </div>
              )}
              <button
                onClick={() => setShowInlineSearch(false)}
                className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded ml-1"
                title="Close search bar"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowInlineSearch(true)}
              className={`px-2.5 py-1 rounded border flex items-center space-x-1 font-medium transition-colors ${
                hasSearch
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
              title="Find text in image (Search)"
            >
              <Search className="w-3.5 h-3.5 text-amber-400" />
              <span>{hasSearch ? `${totalMatchesCount} Match${totalMatchesCount !== 1 ? 'es' : ''}` : 'Find Text'}</span>
            </button>
          )}

          {/* View Controls */}
          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => setShowBoxes(!showBoxes)}
              className={`px-2.5 py-1 rounded border flex items-center space-x-1 font-medium transition-colors ${
                showBoxes
                  ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40'
                  : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
              }`}
              title="Toggle detected bounding box overlay"
            >
              {showBoxes ? <Eye className="w-3.5 h-3.5 text-indigo-400" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span>{showBoxes ? 'Show BBoxes' : 'Hide BBoxes'}</span>
            </button>

            <div className="h-4 w-px bg-slate-800 mx-1" />

            <button
              onClick={handleZoomIn}
              className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            
            <button
              onClick={handleZoomOut}
              className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={handleFitToScreen}
              className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800"
              title="Fit to Screen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={handleResetZoom}
              className="p-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded border border-slate-800"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            <span className="text-[11px] font-mono text-slate-400 min-w-[45px] text-right">
              {Math.round(zoom * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* Workspace */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`flex-1 relative overflow-hidden bg-slate-950 flex items-center justify-center p-6 select-none ${
          isPanning ? 'cursor-grabbing' : 'cursor-grab'
        }`}
      >
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isPanning ? 'none' : 'transform 0.15s ease-out',
          }}
          className="relative inline-block"
        >
          <img
            ref={imgRef}
            src={imageSrc}
            alt="Original Document"
            onLoad={handleImageLoad}
            className="max-w-full max-h-[600px] object-contain rounded shadow-2xl pointer-events-none border border-slate-800/80"
          />

          {showBoxes && imageDimensions.naturalWidth > 0 && (
            <svg
              className="absolute top-0 left-0 w-full h-full pointer-events-auto"
              viewBox={`0 0 ${imageDimensions.naturalWidth} ${imageDimensions.naturalHeight}`}
              preserveAspectRatio="none"
            >
              {regions.map((region) => {
                const isSelected = selectedRegionId === region.id;
                const isSearchMatch = matchingRegionIds.has(region.id);
                const isActiveMatch = activeMatchRegionId === region.id;
                
                const pointsString = region.polygon && region.polygon.length > 0
                  ? region.polygon.map((pt) => `${pt[0]},${pt[1]}`).join(' ')
                  : `${region.bbox[0]},${region.bbox[1]} ${region.bbox[2]},${region.bbox[1]} ${region.bbox[2]},${region.bbox[3]} ${region.bbox[0]},${region.bbox[3]}`;

                // Color calculation
                let color = isSelected
                  ? '#ec4899'
                  : region.confidence >= 0.95
                  ? '#10b981'
                  : region.confidence >= 0.85
                  ? '#3b82f6'
                  : '#f59e0b';

                let strokeWidth = isSelected ? 3 : 1.8;
                let fillOpacity = isSelected ? '40' : '20';
                let opacity = '1';

                if (hasSearch) {
                  if (isActiveMatch) {
                    color = '#fbbf24'; // Gold / bright amber for active search match
                    strokeWidth = 4;
                    fillOpacity = '60';
                  } else if (isSearchMatch) {
                    color = '#f59e0b'; // Amber for search match
                    strokeWidth = 2.8;
                    fillOpacity = '35';
                  } else {
                    opacity = '0.35'; // Dim non-matching regions during search
                  }
                }

                return (
                  <g
                    key={region.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedRegionId(region.id);
                    }}
                    style={{ opacity }}
                    className="cursor-pointer group"
                  >
                    <polygon
                      points={pointsString}
                      fill={`${color}${fillOpacity}`}
                      stroke={color}
                      strokeWidth={strokeWidth}
                      className={`transition-all duration-150 group-hover:fill-amber-500/40 group-hover:stroke-amber-300 ${
                        isActiveMatch ? 'animate-pulse' : ''
                      }`}
                    />
                    {region.bbox && (
                      <text
                        x={region.bbox[0]}
                        y={Math.max(region.bbox[1] - 4, 12)}
                        fill={color}
                        fontSize={Math.max(10, imageDimensions.naturalWidth / 60)}
                        fontWeight="bold"
                        className="font-mono select-none"
                      >
                        {isActiveMatch ? '★ ' : isSearchMatch ? '🔍 ' : ''}#{region.id} ({Math.round(region.confidence * 100)}%)
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          )}
        </div>
      </div>
    </div>
  );
};
