import React, { useState } from 'react';
import { Cpu, FileJson, Table as TableIcon, Tag, AlertTriangle, ChevronRight } from 'lucide-react';
import type { OCRResponse, ExtractedEntity } from '../types';

interface IntelligencePanelProps {
  data: OCRResponse;
  selectedRegionId: number | null;
  setSelectedRegionId: (id: number | null) => void;
}

export const IntelligencePanel: React.FC<IntelligencePanelProps> = ({
  data,
  setSelectedRegionId,
}) => {
  const [subTab, setSubTab] = useState<'entities' | 'tables' | 'json'>('entities');
  const intel = data.intelligence;

  if (!intel) {
    return (
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 text-center text-xs font-mono text-zinc-500">
        Processing document intelligence...
      </div>
    );
  }

  const docType = intel.document_type || 'unknown';
  const entities = intel.entities || [];
  const tables = intel.tables || [];

  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 shadow-xs flex flex-col h-full">
      {/* Document Classification Header */}
      <div className="pb-3 mb-3 border-b border-zinc-800 flex items-center justify-between">
        <div>
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono block">Inferred Document Type</span>
          <span className="text-xs font-bold font-mono text-zinc-100 uppercase tracking-tight flex items-center space-x-1.5 mt-0.5">
            <Cpu className="w-3.5 h-3.5 text-zinc-400" />
            <span>{docType.replace('_', ' ')}</span>
          </span>
        </div>

        <span className="text-[10px] px-2 py-0.5 rounded font-mono border border-zinc-800 bg-zinc-950 text-zinc-300">
          Conf: {Math.round((intel.confidence_score || 0.8) * 100)}%
        </span>
      </div>

      {/* Sub-Tab Navigation */}
      <div className="flex items-center space-x-1 bg-zinc-950 p-1 rounded-lg border border-zinc-800 mb-3 text-xs font-mono">
        <button
          onClick={() => setSubTab('entities')}
          className={`flex-1 py-1 px-2 rounded-md transition-colors flex items-center justify-center space-x-1 ${
            subTab === 'entities'
              ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Tag className="w-3 h-3" />
          <span>Fields ({entities.length})</span>
        </button>

        <button
          onClick={() => setSubTab('tables')}
          className={`flex-1 py-1 px-2 rounded-md transition-colors flex items-center justify-center space-x-1 ${
            subTab === 'tables'
              ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <TableIcon className="w-3 h-3" />
          <span>Tables ({tables.length})</span>
        </button>

        <button
          onClick={() => setSubTab('json')}
          className={`flex-1 py-1 px-2 rounded-md transition-colors flex items-center justify-center space-x-1 ${
            subTab === 'json'
              ? 'bg-zinc-100 text-zinc-950 font-semibold shadow-xs'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <FileJson className="w-3 h-3" />
          <span>JSON</span>
        </button>
      </div>

      {/* Sub-Tab Contents */}
      <div className="flex-1 overflow-y-auto max-h-[420px] pr-1">
        {subTab === 'entities' && (
          <div className="space-y-2">
            {entities.length === 0 ? (
              <div className="text-center py-8 text-xs text-zinc-500 font-mono">
                No dynamic fields extracted.
              </div>
            ) : (
              entities.map((e: ExtractedEntity, idx: number) => (
                <div
                  key={idx}
                  onClick={() => e.source?.bbox && setSelectedRegionId(idx + 1)}
                  className="p-3 rounded-lg border border-zinc-800 bg-zinc-950/60 hover:border-zinc-700 hover:bg-zinc-900/40 transition-colors cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-mono text-zinc-400 font-medium truncate max-w-[170px]">
                      {e.label || e.key}
                    </span>
                    
                    <div className="flex items-center space-x-1 font-mono text-[10px]">
                      {e.needs_review ? (
                        <span className="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center">
                          <AlertTriangle className="w-2.5 h-2.5 mr-0.5" /> Review
                        </span>
                      ) : (
                        <span className="text-zinc-500">
                          {Math.round(e.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-xs font-mono text-zinc-100 bg-zinc-900 p-2 rounded border border-zinc-800/80 break-words">
                    {e.raw_value}
                  </div>

                  {e.normalized_value && String(e.normalized_value) !== e.raw_value && (
                    <div className="mt-1 flex items-center space-x-1 text-[10px] font-mono text-zinc-400">
                      <ChevronRight className="w-3 h-3 text-zinc-500" />
                      <span>Norm: <strong className="text-zinc-200">{String(e.normalized_value)}</strong> {e.currency || ''}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {subTab === 'tables' && (
          <div className="space-y-4">
            {tables.length === 0 ? (
              <div className="text-center py-8 text-xs text-zinc-500 font-mono">
                No structured tables detected in document.
              </div>
            ) : (
              tables.map((t, idx) => (
                <div key={idx} className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 space-y-2">
                  <span className="text-[10px] text-zinc-400 font-mono font-medium block">
                    Table #{t.table_id} (Page {t.page_number})
                  </span>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[11px] font-mono">
                      <thead>
                        <tr className="bg-zinc-900 text-zinc-300 border-b border-zinc-800">
                          {t.headers.map((h, hIdx) => (
                            <th key={hIdx} className="p-1.5 font-semibold">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800/60">
                        {t.rows.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-zinc-900/40">
                            {row.map((cell, cIdx) => (
                              <td key={cIdx} className="p-1.5 text-zinc-300">{String(cell)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {subTab === 'json' && (
          <pre className="bg-zinc-950 p-3 rounded-lg border border-zinc-800 font-mono text-[11px] text-zinc-300 leading-relaxed overflow-x-auto whitespace-pre-wrap select-text">
            {JSON.stringify(intel.structured_json, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};
