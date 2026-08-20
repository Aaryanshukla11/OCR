import React from 'react';
import { Cpu, Zap, Activity, FileSearch, Layers } from 'lucide-react';

interface NavbarProps {
  activeTab: 'tester' | 'history' | 'categories';
  setActiveTab: (tab: 'tester' | 'history' | 'categories') => void;
  device: string;
  isBackendHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  device,
  isBackendHealthy,
}) => {
  const isGpu = device.toUpperCase().includes('GPU');

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-indigo-400/30">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base font-black text-white tracking-wide uppercase font-sans">
                  OUR OCR ENGINE
                </h1>
                <span className="text-[10px] bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-2 py-0.5 rounded font-mono">
                  v1.0.0
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Model Layer: <strong className="text-slate-300">PaddleOCR 3.7.0</strong>
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800/80">
            <button
              onClick={() => setActiveTab('tester')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'tester'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>OCR Workspace</span>
            </button>

            <button
              onClick={() => setActiveTab('categories')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'categories'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <FileSearch className="w-4 h-4" />
              <span>Benchmark Categories</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'history'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Execution Log</span>
            </button>
          </nav>

          {/* Device & Status Indicator */}
          <div className="flex items-center space-x-3">
            <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold ${
              isGpu
                ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 shadow-sm shadow-amber-500/10'
                : 'bg-slate-950 text-slate-300 border-slate-800'
            }`}>
              {isGpu ? (
                <Zap className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
              ) : (
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
              )}
              <span>Device: {device}</span>
            </div>

            <div className="flex items-center space-x-1.5 text-xs text-slate-400 font-mono">
              <span className={`w-2 h-2 rounded-full ${isBackendHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
              <span className="hidden sm:inline">{isBackendHealthy ? 'Pipeline Ready' : 'Connecting...'}</span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
};
