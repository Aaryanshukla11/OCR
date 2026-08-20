import { useState, useEffect, useMemo } from 'react';
import { Navbar, type ActiveTabType } from './components/Navbar';
import { UploadZone } from './components/UploadZone';
import { MetricsCard } from './components/MetricsCard';
import { DocumentViewer } from './components/DocumentViewer';
import { ExtractedTextPanel } from './components/ExtractedTextPanel';
import { DetectionResultsPanel } from './components/DetectionResultsPanel';
import { FindTextPanel, type SearchMatchItem } from './components/FindTextPanel';
import { ComparisonView } from './components/ComparisonView';
import { AccuracyEvalPanel } from './components/AccuracyEvalPanel';
import { CategoryBrowser } from './components/CategoryBrowser';
import { HistoryView } from './components/HistoryView';
import { IntelligencePanel } from './components/IntelligencePanel';
import { DocumentExplorer } from './components/DocumentExplorer';
import { QueryInterface } from './components/QueryInterface';
import type { OCRResponse } from './types';
import { LayoutGrid, Columns, AlertCircle, FileCheck, TestTube, Target, FileSearch, FileText, Cpu } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<ActiveTabType>('tester');
  const [engineMode, setEngineMode] = useState<'ocr' | 'eval'>('ocr');
  const [viewMode, setViewMode] = useState<'inspector' | 'comparison'>('inspector');
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState<string | null>(null);
  const [groundTruthText, setGroundTruthText] = useState<string>('');
  
  const [ocrData, setOcrData] = useState<OCRResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  const [activePageIndex, setActivePageIndex] = useState<number>(0);
  const [selectedRegionId, setSelectedRegionId] = useState<number | null>(null);

  // Right sidebar tab state: 'intelligence' | 'regions' | 'find' | 'text'
  const [rightPanelTab, setRightPanelTab] = useState<'intelligence' | 'regions' | 'find' | 'text'>('intelligence');

  // Search state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isMatchCase, setIsMatchCase] = useState<boolean>(false);
  const [activeMatchIndex, setActiveMatchIndex] = useState<number>(0);

  const [backendDevice, setBackendDevice] = useState<string>('CPU');
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(false);

  // Fetch backend health on mount
  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'healthy') {
          setIsBackendHealthy(true);
          setBackendDevice(data.device || 'CPU');
        }
      })
      .catch(() => setIsBackendHealthy(false));
  }, []);

  const handleInspectStoredDocument = async (docId: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(`/api/documents/${docId}`);
      if (!res.ok) throw new Error('Failed to load stored document intelligence');
      const data = await res.json();
      
      setOcrData({
        filename: data.filename,
        file_type: data.document_type.toUpperCase(),
        total_pages: data.total_pages,
        processing_time: 0.1,
        device: backendDevice,
        average_confidence: data.average_confidence,
        total_regions: data.structured_json?.elements?.length || 10,
        pages: data.structured_json?.pages || [],
        aggregated_text: data.raw_text,
        accuracy: { available: false, message: 'Stored document' },
        status: 'success',
        intelligence: data.structured_json
      });

      if (data.structured_json?.pages?.[0]?.page_image) {
        setImagePreviewUrl(data.structured_json.pages[0].page_image);
      }

      setActiveTab('tester');
    } catch (err: any) {
      alert(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setOcrData(null);
    setErrorMessage(null);
    setActivePageIndex(0);
    setSelectedRegionId(null);
    setSearchQuery('');
    setActiveMatchIndex(0);

    const objectUrl = URL.createObjectURL(file);
    setImagePreviewUrl(objectUrl);
  };

  const handleRunOcr = async () => {
    const fileToProcess = selectedFile;
    if (!fileToProcess) {
      setErrorMessage('Please select a document file first.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    setOcrData(null);
    setActivePageIndex(0);
    setSelectedRegionId(null);
    setSearchQuery('');
    setActiveMatchIndex(0);

    try {
      const formData = new FormData();
      formData.append('file', fileToProcess);

      if (engineMode === 'eval' && groundTruthText.trim()) {
        formData.append('ground_truth', groundTruthText.trim());
      }

      const response = await fetch('/api/ocr', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'OCR processing failed.');
      }

      const resultData: OCRResponse = await response.json();
      setOcrData(resultData);
    } catch (err: any) {
      setErrorMessage(err.message || 'An unexpected error occurred during OCR processing.');
    } finally {
      setIsLoading(false);
    }
  };

  // Compute matching regions for search functionality
  const matchingRegions = useMemo<SearchMatchItem[]>(() => {
    if (!ocrData || !searchQuery.trim()) return [];

    const matches: SearchMatchItem[] = [];
    const queryStr = isMatchCase ? searchQuery : searchQuery.toLowerCase();

    ocrData.pages.forEach((page, pageIdx) => {
      page.regions.forEach((region) => {
        const regionText = isMatchCase ? region.text : region.text.toLowerCase();
        if (regionText.includes(queryStr)) {
          matches.push({
            pageIndex: pageIdx,
            region: region,
          });
        }
      });
    });

    return matches;
  }, [ocrData, searchQuery, isMatchCase]);

  const matchingRegionIds = useMemo(() => {
    return new Set(matchingRegions.map((m) => m.region.id));
  }, [matchingRegions]);

  const activeMatchRegionId = useMemo(() => {
    if (matchingRegions.length === 0) return null;
    const clampedIndex = Math.min(activeMatchIndex, matchingRegions.length - 1);
    return matchingRegions[clampedIndex]?.region.id || null;
  }, [matchingRegions, activeMatchIndex]);

  const handleSearchQueryChange = (query: string) => {
    setSearchQuery(query);
    setActiveMatchIndex(0);
    if (query.trim().length > 0) {
      setRightPanelTab('find');
    }
  };

  const handleNavigateNextMatch = () => {
    if (matchingRegions.length === 0) return;
    const nextIdx = (activeMatchIndex + 1) % matchingRegions.length;
    setActiveMatchIndex(nextIdx);

    const targetPage = matchingRegions[nextIdx].pageIndex;
    if (targetPage !== activePageIndex) {
      setActivePageIndex(targetPage);
    }
    setSelectedRegionId(matchingRegions[nextIdx].region.id);
  };

  const handleNavigatePrevMatch = () => {
    if (matchingRegions.length === 0) return;
    const prevIdx = (activeMatchIndex - 1 + matchingRegions.length) % matchingRegions.length;
    setActiveMatchIndex(prevIdx);

    const targetPage = matchingRegions[prevIdx].pageIndex;
    if (targetPage !== activePageIndex) {
      setActivePageIndex(targetPage);
    }
    setSelectedRegionId(matchingRegions[prevIdx].region.id);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans antialiased selection:bg-zinc-800 selection:text-zinc-100">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        device={backendDevice}
        isBackendHealthy={isBackendHealthy}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Document Explorer Tab */}
        {activeTab === 'explorer' && (
          <DocumentExplorer onSelectDocument={handleInspectStoredDocument} />
        )}

        {/* Natural Language Query Engine Tab */}
        {activeTab === 'query' && (
          <QueryInterface onSelectDocument={handleInspectStoredDocument} />
        )}

        {/* Benchmark Categories Tab */}
        {activeTab === 'categories' && (
          <CategoryBrowser
            onSelectSampleFile={(fileUrl, filename) => {
              fetch(fileUrl)
                .then((r) => r.blob())
                .then((blob) => {
                  const f = new File([blob], filename, { type: blob.type });
                  handleFileSelect(f);
                  setActiveTab('tester');
                });
            }}
          />
        )}

        {/* Execution Log Tab */}
        {activeTab === 'history' && <HistoryView />}

        {/* Primary Workspace Tab */}
        {activeTab === 'tester' && (
          <div className="space-y-6">
            {/* Top Workspace Header */}
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-zinc-100 tracking-tight font-mono">
                  Document Intelligence & OCR Workspace
                </h2>
                <p className="text-xs text-zinc-400 font-mono mt-0.5">
                  Process arbitrary documents with PaddleOCR, extract layout, tables, dynamic entities, and save to SQLite.
                </p>
              </div>

              {/* Engine Mode Toggle */}
              <div className="flex items-center space-x-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800 self-start md:self-auto">
                <button
                  onClick={() => setEngineMode('ocr')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    engineMode === 'ocr'
                      ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <FileCheck className="w-3.5 h-3.5" />
                  <span>Standard OCR & Intelligence</span>
                </button>

                <button
                  onClick={() => setEngineMode('eval')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    engineMode === 'eval'
                      ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                      : 'text-zinc-400 hover:text-zinc-200'
                  }`}
                >
                  <TestTube className="w-3.5 h-3.5" />
                  <span>CER/WER Accuracy Benchmark</span>
                </button>
              </div>
            </div>

            {/* Document Upload Zone */}
            <UploadZone
              selectedFile={selectedFile}
              onFileSelect={handleFileSelect}
              onRunOcr={handleRunOcr}
              isLoading={isLoading}
              groundTruthText={groundTruthText}
              setGroundTruthText={setGroundTruthText}
            />

            {/* Error Feedback Display */}
            {errorMessage && (
              <div className="p-4 bg-zinc-900 border border-red-500/40 rounded-xl text-red-400 text-xs font-mono flex items-center space-x-2 shadow-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* OCR Processing Output Display */}
            {ocrData && imagePreviewUrl && (
              <div className="space-y-6">
                {/* Executive Summary Metrics Card */}
                <MetricsCard data={ocrData} />

                {/* View Mode Bar */}
                <div className="flex items-center justify-between bg-zinc-900/60 p-2.5 rounded-xl border border-zinc-800">
                  <div className="text-xs font-semibold text-zinc-300 font-mono flex items-center space-x-2">
                    <LayoutGrid className="w-4 h-4 text-zinc-400" />
                    <span>DOCUMENT ANALYSIS VIEW</span>
                  </div>

                  <div className="flex items-center space-x-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800">
                    <button
                      onClick={() => setViewMode('inspector')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        viewMode === 'inspector'
                          ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                          : 'text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      <LayoutGrid className="w-3.5 h-3.5" />
                      <span>Bounding Box Inspector</span>
                    </button>

                    <button
                      onClick={() => setViewMode('comparison')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                        viewMode === 'comparison'
                          ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                          : 'text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      <Columns className="w-3.5 h-3.5" />
                      <span>2-Panel Comparison</span>
                    </button>
                  </div>
                </div>

                {/* View Mode A: Bounding Box Inspector Layout */}
                {viewMode === 'inspector' && (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left Column: Interactive Image Document Viewer */}
                    <div className="lg:col-span-2 min-h-[550px]">
                      <DocumentViewer
                        imageSrc={imagePreviewUrl}
                        pageResults={ocrData.pages}
                        activePageIndex={activePageIndex}
                        setActivePageIndex={setActivePageIndex}
                        selectedRegionId={selectedRegionId}
                        setSelectedRegionId={setSelectedRegionId}
                        searchQuery={searchQuery}
                        setSearchQuery={handleSearchQueryChange}
                        matchingRegionIds={matchingRegionIds}
                        activeMatchRegionId={activeMatchRegionId}
                        onNavigateNextMatch={handleNavigateNextMatch}
                        onNavigatePrevMatch={handleNavigatePrevMatch}
                        totalMatchesCount={matchingRegions.length}
                        currentMatchIndex={activeMatchIndex}
                      />
                    </div>

                    {/* Right Column: Tabbed Workspace Sidebar */}
                    <div className="flex flex-col space-y-4 min-h-[550px]">
                      {/* Sidebar Tab Header */}
                      <div className="flex items-center space-x-1 bg-zinc-900/60 p-1 rounded-lg border border-zinc-800">
                        <button
                          onClick={() => setRightPanelTab('intelligence')}
                          className={`flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
                            rightPanelTab === 'intelligence'
                              ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                              : 'text-zinc-400 hover:text-zinc-200'
                          }`}
                        >
                          <Cpu className="w-3.5 h-3.5" />
                          <span>Intelligence</span>
                        </button>

                        <button
                          onClick={() => setRightPanelTab('regions')}
                          className={`flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
                            rightPanelTab === 'regions'
                              ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                              : 'text-zinc-400 hover:text-zinc-200'
                          }`}
                        >
                          <Target className="w-3.5 h-3.5" />
                          <span>Regions</span>
                        </button>

                        <button
                          onClick={() => setRightPanelTab('find')}
                          className={`flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
                            rightPanelTab === 'find'
                              ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                              : 'text-zinc-400 hover:text-zinc-200'
                          }`}
                        >
                          <FileSearch className="w-3.5 h-3.5" />
                          <span>Find</span>
                          {matchingRegions.length > 0 && (
                            <span className="ml-1 text-[10px] bg-zinc-800 text-zinc-300 font-mono px-1.5 py-0.2 rounded border border-zinc-700">
                              {matchingRegions.length}
                            </span>
                          )}
                        </button>

                        <button
                          onClick={() => setRightPanelTab('text')}
                          className={`flex-1 flex items-center justify-center space-x-1 py-1.5 rounded-md text-xs font-medium transition-colors ${
                            rightPanelTab === 'text'
                              ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                              : 'text-zinc-400 hover:text-zinc-200'
                          }`}
                        >
                          <FileText className="w-3.5 h-3.5" />
                          <span>Full Text</span>
                        </button>
                      </div>

                      {/* Active Sidebar Tab View */}
                      <div className="flex-1">
                        {rightPanelTab === 'intelligence' && (
                          <IntelligencePanel
                            data={ocrData}
                            selectedRegionId={selectedRegionId}
                            setSelectedRegionId={setSelectedRegionId}
                          />
                        )}

                        {rightPanelTab === 'regions' && (
                          <DetectionResultsPanel
                            pageResult={ocrData.pages[activePageIndex] || ocrData.pages[0]}
                            selectedRegionId={selectedRegionId}
                            setSelectedRegionId={setSelectedRegionId}
                          />
                        )}

                        {rightPanelTab === 'find' && (
                          <FindTextPanel
                            data={ocrData}
                            activePageIndex={activePageIndex}
                            setActivePageIndex={setActivePageIndex}
                            selectedRegionId={selectedRegionId}
                            setSelectedRegionId={setSelectedRegionId}
                            searchQuery={searchQuery}
                            setSearchQuery={setSearchQuery}
                            isMatchCase={isMatchCase}
                            setIsMatchCase={setIsMatchCase}
                            activeMatchIndex={activeMatchIndex}
                            setActiveMatchIndex={setActiveMatchIndex}
                            matchingRegions={matchingRegions}
                          />
                        )}

                        {rightPanelTab === 'text' && (
                          <ExtractedTextPanel data={ocrData} />
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* View Mode B: Two-Panel Comparison Mode */}
                {viewMode === 'comparison' && (
                  <div className="space-y-6">
                    <ComparisonView imageSrc={imagePreviewUrl} data={ocrData} />
                    <AccuracyEvalPanel accuracy={ocrData.accuracy} />
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Modern Sleek Minimalist Footer */}
      <footer className="border-t border-zinc-800/80 bg-zinc-950 py-4 text-center text-xs text-zinc-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            Document Intelligence Platform Engine • PaddleOCR 3.7.0 • PPStructureV3 Architecture
          </div>
          <div className="text-zinc-600">
            Powered by Antigravity AI
          </div>
        </div>
      </footer>
    </div>
  );
}
