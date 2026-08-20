import React, { useState } from 'react';
import { MessageSquare, Sparkles, Search, Code, CheckCircle, FileText, ArrowRight } from 'lucide-react';
import type { QueryResponse } from '../types';

interface QueryInterfaceProps {
  onSelectDocument: (docId: string) => void;
}

export const QueryInterface: React.FC<QueryInterfaceProps> = ({ onSelectDocument }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunQuery = async (queryText: string) => {
    if (!queryText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText.trim() }),
      });
      if (!res.ok) throw new Error('Query execution failed');
      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Error executing query');
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    "Show me all invoices from August",
    "How much did I spend on food?",
    "Which flights did Aaryan take in August?",
    "Find documents containing GST number",
    "Give me all hotel bookings",
  ];

  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-6 shadow-xs max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="pb-4 border-b border-zinc-800">
        <h2 className="text-base font-bold text-zinc-100 font-mono flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-zinc-400" />
          <span>Natural Language Document Query Engine</span>
        </h2>
        <p className="text-xs text-zinc-400 font-mono mt-1">
          Ask questions in natural language. The query planner translates questions into structured SQLite parameters.
        </p>
      </div>

      {/* Query Search Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleRunQuery(query);
        }}
        className="flex items-center space-x-3"
      >
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-zinc-500 absolute left-3.5 top-3" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask something about your documents (e.g., 'How much did I spend on food in August?')..."
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-zinc-600 font-mono shadow-xs"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="bg-zinc-100 hover:bg-white text-zinc-950 font-semibold px-5 py-2.5 rounded-xl text-xs font-mono transition-colors disabled:opacity-50 flex items-center space-x-1.5 shadow-xs"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{loading ? 'Processing...' : 'Ask Query'}</span>
        </button>
      </form>

      {/* Sample Query Suggestions */}
      <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
        <span className="text-[11px] text-zinc-500 font-medium">Sample Queries:</span>
        {sampleQueries.map((sample, idx) => (
          <button
            key={idx}
            onClick={() => {
              setQuery(sample);
              handleRunQuery(sample);
            }}
            className="px-2.5 py-1 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 transition-colors text-[11px]"
          >
            "{sample}"
          </button>
        ))}
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-xs font-mono text-red-400">
          {error}
        </div>
      )}

      {/* Query Results Display */}
      {result && (
        <div className="space-y-6 pt-4 border-t border-zinc-800">
          {/* Answer Banner */}
          <div className="bg-zinc-950 p-5 rounded-xl border border-zinc-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-mono font-semibold flex items-center space-x-1.5">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>QUERY ANSWER SUMMARY</span>
              </span>

              {result.aggregated_value !== null && result.aggregated_value !== undefined && (
                <span className="text-xs font-mono font-bold bg-zinc-900 px-3 py-1 rounded border border-zinc-800 text-zinc-100">
                  {result.plan.aggregation}: {String(result.aggregated_value)}
                </span>
              )}
            </div>

            <p className="text-sm font-mono text-zinc-200 font-semibold leading-relaxed">
              {result.answer_summary}
            </p>

            {/* Executed SQL Plan Box */}
            <div className="pt-2 border-t border-zinc-800/80">
              <span className="text-[10px] text-zinc-500 font-mono block mb-1 flex items-center space-x-1">
                <Code className="w-3 h-3 text-zinc-500" />
                <span>Validated Parameterized SQL Query Executed:</span>
              </span>
              <code className="text-[11px] font-mono text-zinc-400 bg-zinc-900 p-2.5 rounded border border-zinc-800 block overflow-x-auto select-text">
                {result.plan.sql_executed}
              </code>
            </div>
          </div>

          {/* Matching Documents List */}
          <div>
            <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono mb-3">
              Matching Documents ({result.documents.length})
            </h3>

            {result.documents.length === 0 ? (
              <div className="text-center py-8 text-xs font-mono text-zinc-500 bg-zinc-950 rounded-xl border border-zinc-800">
                No matching documents found in SQLite database.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => onSelectDocument(doc.id)}
                    className="p-3.5 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-xl transition-all cursor-pointer flex items-center justify-between group"
                  >
                    <div className="flex items-center space-x-3 truncate">
                      <FileText className="w-4 h-4 text-zinc-400 shrink-0" />
                      <div className="truncate">
                        <h4 className="text-xs font-mono font-semibold text-zinc-200 truncate group-hover:text-white">
                          {doc.title_highlight}
                        </h4>
                        <div className="flex items-center space-x-2 text-[10px] font-mono text-zinc-500 mt-0.5">
                          <span className="uppercase">{doc.document_type}</span>
                          <span>•</span>
                          <span>Conf: {doc.average_confidence}%</span>
                        </div>
                      </div>
                    </div>

                    <ArrowRight className="w-4 h-4 text-zinc-500 group-hover:text-zinc-200 transition-transform group-hover:translate-x-0.5" />
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
