import { useState, useEffect, useMemo } from 'react';
import { Navbar } from './components/Navbar';
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
import type { OCRResponse } from './types';
import { LayoutGrid, Columns, AlertCircle, FileCheck, TestTube, Target, FileSearch, FileText } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'tester' | 'history' | 'categories'>('tester');
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

  // Right sidebar tab state: 'regions' | 'find' | 'text'
  const [rightPanelTab, setRightPanelTab] = useState<'regions' | 'find' | 'text'>('regions');

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
      .catch((err) => {
        console.error('Health check failed:', err);
        setIsBackendHealthy(false);
      });
  }, []);

  // Calculate search matches across all pages
  const matchingRegions = useMemo(() => {
    if (!ocrData || !searchQuery.trim()) return [];
    const query = isMatchCase ? searchQuery : searchQuery.toLowerCase();
    const matches: SearchMatchItem[] = [];

    ocrData.pages?.forEach((page, pageIdx) => {
      page.regions?.forEach((region) => {
        const text = isMatchCase ? region.text : region.text.toLowerCase();
        if (text.includes(query)) {
          matches.push({ pageIndex: pageIdx, region });
        }
      });
    });

    return matches;
  }, [ocrData, searchQuery, isMatchCase]);

  // When search query changes, reset match index and select first match
  useEffect(() => {
    setActiveMatchIndex(0);
    if (matchingRegions.length > 0) {
      const firstMatch = matchingRegions[0];
      setActivePageIndex(firstMatch.pageIndex);
      setSelectedRegionId(firstMatch.region.id);
    }
  }, [searchQuery, isMatchCase]);

  // Compute set of region IDs matching on current page
  const matchingRegionIds = useMemo(() => {
    const set = new Set<number>();
    matchingRegions.forEach((m) => {
      if (m.pageIndex === activePageIndex) {
        set.add(m.region.id);
      }
    });
    return set;
  }, [matchingRegions, activePageIndex]);

  const activeMatch = matchingRegions[activeMatchIndex];
  const activeMatchRegionId =
    activeMatch && activeMatch.pageIndex === activePageIndex
      ? activeMatch.region.id
      : null;

  const handleNavigateNextMatch = () => {
    if (matchingRegions.length === 0) return;
    const nextIdx = (activeMatchIndex + 1) % matchingRegions.length;
    setActiveMatchIndex(nextIdx);
    const match = matchingRegions[nextIdx];
    if (match) {
      setActivePageIndex(match.pageIndex);
      setSelectedRegionId(match.region.id);
    }
  };

  const handleNavigatePrevMatch = () => {
    if (matchingRegions.length === 0) return;
    const prevIdx = (activeMatchIndex - 1 + matchingRegions.length) % matchingRegions.length;
    setActiveMatchIndex(prevIdx);
    const match = matchingRegions[prevIdx];
    if (match) {
      setActivePageIndex(match.pageIndex);
      setSelectedRegionId(match.region.id);
    }
  };

  const handleSearchQueryChange = (query: string) => {
    setSearchQuery(query);
    if (query.trim()) {
      setRightPanelTab('find');
    }
  };

  const handleRunOcr = async (fileToProcess: File, gtText?: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    setSelectedFile(fileToProcess);
    
    // Create preview URL
    const objectUrl = URL.createObjectURL(fileToProcess);
    setImagePreviewUrl(objectUrl);

    const formData = new FormData();
    formData.append('file', fileToProcess);
    
    // Pass ground truth if in evaluation mode or explicitly provided
    if ((engineMode === 'eval' || gtText) && (gtText || groundTruthText).trim()) {
      formData.append('ground_truth', (gtText || groundTruthText).trim());
    }

    try {
      const response = await fetch('/api/ocr', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'OCR Engine processing failed');
      }

      const result: OCRResponse = await response.json();
      setOcrData(result);
      setActivePageIndex(0);
      setSelectedRegionId(null);
      setSearchQuery('');
    } catch (err: any) {
      console.error('OCR Engine API Error:', err);
      setErrorMessage(err.message || 'An error occurred while running OCR Engine.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectSampleFromCategory = async (category: string, filename: string) => {
    setActiveTab('tester');
    setEngineMode('eval');
    setIsLoading(true);
    setErrorMessage(null);

    const fileUrl = `/api/test-data/${category}/${filename}`;
    const gtUrl = `/api/test-data-gt/${category}/${filename}`;

    try {
      const [fileRes, gtRes] = await Promise.all([
        fetch(fileUrl),
        fetch(gtUrl).then((r) => r.json()).catch(() => ({ ground_truth: null })),
      ]);

      if (!fileRes.ok) throw new Error('Failed to load sample file');
      
      const blob = await fileRes.blob();
      const sampleFile = new File([blob], filename, { type: blob.type || 'image/png' });
      const gtContent = gtRes.ground_truth || '';

      setSelectedFile(sampleFile);
      setGroundTruthText(gtContent);
      
      await handleRunOcr(sampleFile, gtContent);
    } catch (err: any) {
      setErrorMessage(`Failed to load category sample: ${err.message}`);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        device={backendDevice}
        isBackendHealthy={isBackendHealthy}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Error Notification */}
        {errorMessage && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-4 rounded-xl flex items-center justify-between shadow-lg">
            <div className="flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <div>
                <p className="text-xs font-bold uppercase tracking-wider">Engine Processing Error</p>
                <p className="text-xs font-mono">{errorMessage}</p>
              </div>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-xs bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 px-3 py-1 rounded"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Tab 1: OCR Engine Main Dashboard */}
        {activeTab === 'tester' && (
          <div className="space-y-6">
            
            {/* Mode Switcher Bar */}
            <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Engine Mode:
                </span>
                
                <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800">
                  <button
                    onClick={() => setEngineMode('ocr')}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-all ${
                      engineMode === 'ocr'
                        ? 'bg-indigo-600 text-white shadow'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <FileCheck className="w-3.5 h-3.5" />
                    <span>1. Production OCR Mode</span>
                  </button>

                  <button
                    onClick={() => setEngineMode('eval')}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-all ${
                      engineMode === 'eval'
                        ? 'bg-indigo-600 text-white shadow'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <TestTube className="w-3.5 h-3.5" />
                    <span>2. Benchmark Evaluation Mode</span>
                  </button>
                </div>
              </div>

              <div className="text-[11px] text-slate-400 font-mono">
                {engineMode === 'ocr'
                  ? 'Standard Document & Image Text Extraction'
                  : 'Ground Truth Accuracy Benchmark (CER / WER Metrics)'}
              </div>
            </div>

            {/* Upload Area */}
            <UploadZone
              onFileSelect={(file, gt) => handleRunOcr(file, gt || groundTruthText)}
              isLoading={isLoading}
              selectedFile={selectedFile}
              groundTruthText={groundTruthText}
              setGroundTruthText={setGroundTruthText}
            />

            {/* Results Section */}
            {ocrData && imagePreviewUrl && (
              <div className="space-y-6 animate-fade-in">
                
                {/* Metrics Card Bar */}
                <MetricsCard data={ocrData} />

                {/* View Mode Selector Header */}
                <div className="flex items-center justify-between bg-slate-900 px-4 py-2.5 rounded-xl border border-slate-800">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                    Document Workspace ({ocrData.filename})
                  </span>

                  <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                    <button
                      onClick={() => setViewMode('inspector')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-all ${
                        viewMode === 'inspector'
                          ? 'bg-indigo-600 text-white shadow'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <LayoutGrid className="w-3.5 h-3.5" />
                      <span>Bounding Box Inspector</span>
                    </button>

                    <button
                      onClick={() => setViewMode('comparison')}
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-semibold transition-all ${
                        viewMode === 'comparison'
                          ? 'bg-indigo-600 text-white shadow'
                          : 'text-slate-400 hover:text-slate-200'
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

                    {/* Right Column: Tabbed Workspace Sidebar (Detection Regions / Find in Image / Extracted Text) */}
                    <div className="flex flex-col space-y-4 min-h-[550px]">
                      {/* Sidebar Tab Header */}
                      <div className="flex items-center space-x-1 bg-slate-900 p-1 rounded-xl border border-slate-800">
                        <button
                          onClick={() => setRightPanelTab('regions')}
                          className={`flex-1 flex items-center justify-center space-x-1.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                            rightPanelTab === 'regions'
                              ? 'bg-indigo-600 text-white shadow'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-950/40'
                          }`}
                        >
                          <Target className="w-3.5 h-3.5" />
                          <span>Regions</span>
                        </button>

                        <button
                          onClick={() => setRightPanelTab('find')}
                          className={`flex-1 flex items-center justify-center space-x-1.5 py-2 rounded-lg text-xs font-semibold transition-all relative ${
                            rightPanelTab === 'find'
                              ? 'bg-amber-600 text-white shadow'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-950/40'
                          }`}
                        >
                          <FileSearch className="w-3.5 h-3.5" />
                          <span>Find</span>
                          {matchingRegions.length > 0 && (
                            <span className="ml-1 text-[10px] bg-amber-400/20 text-amber-300 font-mono px-1.5 py-0.2 rounded-full border border-amber-400/40">
                              {matchingRegions.length}
                            </span>
                          )}
                        </button>

                        <button
                          onClick={() => setRightPanelTab('text')}
                          className={`flex-1 flex items-center justify-center space-x-1.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                            rightPanelTab === 'text'
                              ? 'bg-indigo-600 text-white shadow'
                              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-950/40'
                          }`}
                        >
                          <FileText className="w-3.5 h-3.5" />
                          <span>Full Text</span>
                        </button>
                      </div>

                      {/* Active Sidebar Tab View */}
                      <div className="flex-1">
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

        {/* Tab 2: Test Dataset Categories */}
        {activeTab === 'categories' && (
          <CategoryBrowser onSelectSampleFile={handleSelectSampleFromCategory} />
        )}

        {/* Tab 3: Local Test History */}
        {activeTab === 'history' && (
          <HistoryView />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 space-y-2 sm:space-y-0 font-mono">
          <div>
            OUR OCR ENGINE v1.0.0 • Decoupled Model Layer Architecture
          </div>
          <div className="flex items-center space-x-4 text-slate-400">
            <span>Model: PaddleOCR 3.7.0</span>
            <span>•</span>
            <span>REST API Active</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
