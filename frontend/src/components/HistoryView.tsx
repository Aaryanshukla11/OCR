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
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 shadow-xs">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center space-x-2 font-mono">
            <History className="w-4 h-4 text-zinc-400" />
            <span>Local Evaluation Test Run History</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Historical log of all previous PaddleOCR test evaluations performed on this machine.
          </p>
        </div>

        {history.length > 0 && (
          <button
            onClick={handleClearHistory}
            className="px-3 py-1.5 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 rounded-md border border-zinc-800 text-xs font-medium flex items-center space-x-1.5 transition-colors font-mono"
          >
            <Trash2 className="w-3.5 h-3.5 text-zinc-400" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-xs text-zinc-500 font-mono">Loading history logs...</div>
      ) : history.length === 0 ? (
        <div className="text-center py-12 text-zinc-500 bg-zinc-950 rounded-lg border border-zinc-800 font-mono">
          <History className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
          <p className="text-xs">No test runs recorded yet. Upload a document to start testing.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="bg-zinc-950 text-zinc-400 border-b border-zinc-800 uppercase tracking-wider text-[10px]">
                <th className="p-3">Filename</th>
                <th className="p-3">Date / Time</th>
                <th className="p-3">Device</th>
                <th className="p-3">Latency</th>
                <th className="p-3">Regions</th>
                <th className="p-3">Avg Conf</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/80">
              {history.map((item) => {
                const isGpu = item.device.toUpperCase().includes('GPU');
                return (
                  <tr key={item.id} className="hover:bg-zinc-950/60 transition-colors">
                    <td className="p-3 font-medium text-zinc-200 flex items-center space-x-2">
                      <FileText className="w-3.5 h-3.5 text-zinc-400" />
                      <span className="truncate max-w-[200px]">{item.filename}</span>
                    </td>
                    <td className="p-3 text-zinc-400">{item.timestamp}</td>
                    <td className="p-3">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] bg-zinc-900 border border-zinc-800 text-zinc-300 font-mono">
                        {isGpu ? <Zap className="w-3 h-3 text-zinc-300 mr-1" /> : <Cpu className="w-3 h-3 text-zinc-400 mr-1" />}
                        {item.device}
                      </span>
                    </td>
                    <td className="p-3 text-zinc-300">{item.processing_time}s</td>
                    <td className="p-3 text-zinc-300">{item.total_regions}</td>
                    <td className="p-3 text-zinc-200 font-semibold">{item.average_confidence}%</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono border border-zinc-800 bg-zinc-900 text-zinc-300">
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

