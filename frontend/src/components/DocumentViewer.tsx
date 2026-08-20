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
  const currentImageSrc = currentPage?.page_image || imageSrc;
  const isRawPdfBlob = !currentPage?.page_image && (imageSrc.includes('.pdf') || (imageSrc.startsWith('blob:') && !currentPage));

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
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden shadow-xs flex flex-col h-full">
      {/* Control Bar */}
      <div className="bg-zinc-950 px-4 py-2 border-b border-zinc-800 flex flex-wrap items-center justify-between text-xs select-none gap-2">
        
        {/* Title & Page Nav */}
        <div className="flex items-center space-x-3">
          <span className="font-medium text-zinc-200 flex items-center space-x-1.5 font-mono">
            <Layers className="w-3.5 h-3.5 text-zinc-400" />
            <span>Document Viewer</span>
          </span>

          {pageResults.length > 1 && (
            <div className="flex items-center space-x-1.5 bg-zinc-900 px-2 py-1 rounded-md border border-zinc-800">
              <button
                disabled={activePageIndex === 0}
                onClick={() => setActivePageIndex(activePageIndex - 1)}
                className="p-0.5 text-zinc-400 hover:text-zinc-100 disabled:opacity-30 disabled:hover:text-zinc-400"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-zinc-300 font-mono text-xs">
                Page {activePageIndex + 1} of {pageResults.length}
              </span>
              <button
                disabled={activePageIndex === pageResults.length - 1}
                onClick={() => setActivePageIndex(activePageIndex + 1)}
                className="p-0.5 text-zinc-400 hover:text-zinc-100 disabled:opacity-30 disabled:hover:text-zinc-400"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Search Bar / Find Controls */}
        <div className="flex items-center space-x-2">
          {showInlineSearch && setSearchQuery ? (
            <div className="flex items-center space-x-1 bg-zinc-900 px-2 py-1 rounded-md border border-zinc-700">
              <Search className="w-3.5 h-3.5 text-zinc-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Find in image..."
                className="bg-transparent text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none w-32 sm:w-44 font-mono"
                autoFocus
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="text-zinc-400 hover:text-zinc-100 p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
              {totalMatchesCount > 0 && (
                <div className="flex items-center space-x-1 pl-1 border-l border-zinc-800 text-[10px] font-mono text-zinc-300">
                  <span>{currentMatchIndex + 1}/{totalMatchesCount}</span>
                  <button
                    onClick={onNavigatePrevMatch}
                    className="hover:text-zinc-100 p-0.5"
                    title="Previous match"
                  >
                    <ChevronUp className="w-3 h-3" />
                  </button>
                  <button
                    onClick={onNavigateNextMatch}
                    className="hover:text-zinc-100 p-0.5"
                    title="Next match"
                  >
                    <ChevronDown className="w-3 h-3" />
                  </button>
                </div>
              )}
              <button
                onClick={() => setShowInlineSearch(false)}
                className="p-1 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 rounded ml-1"
                title="Close search bar"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => setShowInlineSearch(true)}
              className={`px-2.5 py-1 rounded-md border flex items-center space-x-1 font-medium transition-colors ${
                hasSearch
                  ? 'bg-zinc-800 text-zinc-200 border-zinc-700'
                  : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200 hover:bg-zinc-800/60'
              }`}
              title="Find text in image (Search)"
            >
              <Search className="w-3.5 h-3.5 text-zinc-400" />
              <span>{hasSearch ? `${totalMatchesCount} Match${totalMatchesCount !== 1 ? 'es' : ''}` : 'Find Text'}</span>
            </button>
          )}

          {/* View Controls */}
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setShowBoxes(!showBoxes)}
              className={`px-2.5 py-1 rounded-md border flex items-center space-x-1 font-medium transition-colors ${
                showBoxes
                  ? 'bg-zinc-800 text-zinc-200 border-zinc-700'
                  : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200 hover:bg-zinc-800/60'
              }`}
              title="Toggle detected bounding box overlay"
            >
              {showBoxes ? <Eye className="w-3.5 h-3.5 text-zinc-300" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span>{showBoxes ? 'BBoxes On' : 'BBoxes Off'}</span>
            </button>

            <div className="h-4 w-px bg-zinc-800 mx-1" />

            <button
              onClick={handleZoomIn}
              className="p-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-md border border-zinc-800"
              title="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            
            <button
              onClick={handleZoomOut}
              className="p-1.5 bg-zinc-900 hover:bg-slate-800 text-zinc-300 rounded-md border border-zinc-800"
              title="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={handleFitToScreen}
              className="p-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-md border border-zinc-800"
              title="Fit to Screen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={handleResetZoom}
              className="p-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-md border border-zinc-800"
              title="Reset Zoom"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>

            <span className="text-[11px] font-mono text-zinc-500 min-w-[42px] text-right">
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
        className={`flex-1 relative overflow-hidden bg-zinc-950 flex items-center justify-center p-6 select-none ${
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
          {isRawPdfBlob ? (
            <object
              data={imageSrc}
              type="application/pdf"
              className="w-[650px] h-[550px] max-w-full rounded border border-zinc-800 bg-zinc-900"
            >
              <embed src={imageSrc} type="application/pdf" className="w-full h-full" />
            </object>
          ) : (
            <img
              ref={imgRef}
              src={currentImageSrc}
              alt="Original Document"
              onLoad={handleImageLoad}
              className="max-w-full max-h-[600px] object-contain rounded border border-zinc-800 pointer-events-none"
            />
          )}


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
                  ? '#ffffff'
                  : region.confidence >= 0.95
                  ? '#10b981'
                  : region.confidence >= 0.85
                  ? '#a1a1aa'
                  : '#f59e0b';

                let strokeWidth = isSelected ? 2.5 : 1.5;
                let fillOpacity = isSelected ? '30' : '15';
                let opacity = '1';

                if (hasSearch) {
                  if (isActiveMatch) {
                    color = '#f59e0b'; // Crisp amber for active search match
                    strokeWidth = 3.5;
                    fillOpacity = '50';
                  } else if (isSearchMatch) {
                    color = '#d97706';
                    strokeWidth = 2.5;
                    fillOpacity = '30';
                  } else {
                    opacity = '0.25'; // Dim non-matching regions
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
                      className="transition-all duration-150 group-hover:fill-zinc-100/30 group-hover:stroke-white"
                    />
                    {region.bbox && (
                      <text
                        x={region.bbox[0]}
                        y={Math.max(region.bbox[1] - 4, 12)}
                        fill={color}
                        fontSize={Math.max(10, imageDimensions.naturalWidth / 60)}
                        fontWeight="600"
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

