import React from 'react';
import { Cpu, Zap, Activity, FileSearch, Layers, Database, MessageSquare } from 'lucide-react';

export type ActiveTabType = 'tester' | 'explorer' | 'query' | 'categories' | 'history';

interface NavbarProps {
  activeTab: ActiveTabType;
  setActiveTab: (tab: ActiveTabType) => void;
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
    <header className="bg-zinc-950/90 backdrop-blur-md border-b border-zinc-800/80 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-100">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-sm font-semibold text-zinc-100 tracking-tight font-sans">
                  Document Intelligence Platform
                </h1>
                <span className="text-[10px] bg-zinc-900 text-zinc-400 border border-zinc-800 px-1.5 py-0.5 rounded font-mono">
                  v2.0
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 bg-zinc-900/60 p-1 rounded-lg border border-zinc-800/80">
            <button
              onClick={() => setActiveTab('tester')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'tester'
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Workspace</span>
            </button>

            <button
              onClick={() => setActiveTab('explorer')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'explorer'
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Structured Data Store</span>
            </button>

            <button
              onClick={() => setActiveTab('query')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'query'
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>NL Query</span>
            </button>

            <button
              onClick={() => setActiveTab('categories')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'categories'
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
            >
              <FileSearch className="w-3.5 h-3.5" />
              <span>Benchmark Categories</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === 'history'
                  ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Execution Log</span>
            </button>
          </nav>

          {/* Device & Status Indicator */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300">
              {isGpu ? (
                <Zap className="w-3.5 h-3.5 text-zinc-300" />
              ) : (
                <Cpu className="w-3.5 h-3.5 text-zinc-400" />
              )}
              <span>{device}</span>
            </div>

            <div className="flex items-center space-x-1.5 text-xs text-zinc-400 font-mono">
              <span className={`w-2 h-2 rounded-full ${isBackendHealthy ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              <span className="hidden sm:inline">{isBackendHealthy ? 'Ready' : 'Offline'}</span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
};
