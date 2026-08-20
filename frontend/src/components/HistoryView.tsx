import React, { useEffect, useState } from 'react';
import { History, Trash2, Cpu, Zap, FileText } from 'lucide-react';
import type { HistoryItem } from '../types';

export const HistoryView: React.FC = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = () => {
    fetch('/api/history')
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setHistory(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to fetch history:', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear test execution history?')) {
      fetch('/api/history', { method: 'DELETE' })
        .then(() => fetchHistory())
        .catch(console.error);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <History className="w-4 h-4 text-indigo-400" />
            <span>Local Evaluation Test Run History</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Historical log of all previous PaddleOCR test evaluations performed on this machine.
          </p>
        </div>

        {history.length > 0 && (
          <button
            onClick={handleClearHistory}
            className="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 rounded border border-rose-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-xs text-slate-500">Loading history logs...</div>
      ) : history.length === 0 ? (
        <div className="text-center py-12 text-slate-500 bg-slate-950 rounded-lg border border-slate-800">
          <History className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-xs">No test runs recorded yet. Upload a document to start testing.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
                <th className="p-3">Filename</th>
                <th className="p-3">Date / Time</th>
                <th className="p-3">Device</th>
                <th className="p-3">Processing Time</th>
                <th className="p-3">Regions</th>
                <th className="p-3">Avg Confidence</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {history.map((item) => {
                const isGpu = item.device.toUpperCase().includes('GPU');
                return (
                  <tr key={item.id} className="hover:bg-slate-950/60 transition-colors">
                    <td className="p-3 font-semibold text-slate-200 flex items-center space-x-2">
                      <FileText className="w-3.5 h-3.5 text-indigo-400" />
                      <span className="truncate max-w-[200px]">{item.filename}</span>
                    </td>
                    <td className="p-3 text-slate-400">{item.timestamp}</td>
                    <td className="p-3">
                      <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-bold ${
                        isGpu ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30' : 'bg-slate-800 text-slate-300'
                      }`}>
                        {isGpu ? <Zap className="w-3 h-3 text-amber-400 mr-1" /> : <Cpu className="w-3 h-3 text-slate-400 mr-1" />}
                        {item.device}
                      </span>
                    </td>
                    <td className="p-3 text-emerald-400">{item.processing_time}s</td>
                    <td className="p-3 text-cyan-300">{item.total_regions} regions</td>
                    <td className="p-3 text-purple-300 font-bold">{item.average_confidence}%</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                        item.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      }`}>
                        {item.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
