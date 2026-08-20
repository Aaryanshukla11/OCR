import React, { useState, useEffect } from 'react';
import { Database, Search, Trash2, Eye, Cpu, AlertCircle, CheckCircle2 } from 'lucide-react';
import type { StructuredInformationSummary } from '../types';

interface StructuredDataStoreProps {
  onSelectDocument: (docId: string) => void;
}

export const StructuredDataStore: React.FC<StructuredDataStoreProps> = ({ onSelectDocument }) => {
  const [items, setItems] = useState<StructuredInformationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);

  const fetchItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedType !== 'all') params.append('document_type', selectedType);
      if (search.trim()) params.append('search', search.trim());

      const res = await fetch(`http://localhost:8000/api/documents?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to fetch structured information from SQLite database');
      const data = await res.json();
      setItems(data.documents || []);
    } catch (err: any) {
      setError(err.message || 'Error loading structured information');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [selectedType]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchItems();
  };

  const handleDelete = async (docId: string, title: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm(`Delete structured record "${title}" from SQLite database?`)) return;

    try {
      const res = await fetch(`http://localhost:8000/api/documents/${docId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to delete structured record');
      fetchItems();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const docTypes = ['all', 'invoice', 'receipt', 'flight_ticket', 'hotel_invoice', 'bank_statement', 'medical_report', 'contract', 'unknown'];

  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-6 shadow-xs max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-zinc-800">
        <div>
          <h2 className="text-base font-bold text-zinc-100 font-mono flex items-center space-x-2">
            <Database className="w-5 h-5 text-zinc-400" />
            <span>Extracted Structured Knowledge Store</span>
          </h2>
          <p className="text-xs text-zinc-400 font-mono mt-1">
            SQLite stores ONLY extracted structured information (key-value fields, normalized data, tables, and relationships). Original uploaded files are processed strictly as temporary inputs and discarded.
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex items-center space-x-2">
          <div className="relative">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search extracted entity values..."
              className="bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono w-64"
            />
          </div>
          <button
            type="submit"
            className="bg-zinc-100 text-zinc-950 font-semibold px-3 py-1.5 rounded-lg text-xs font-mono hover:bg-white transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Filter Category Pills */}
      <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
        {docTypes.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            className={`px-3 py-1 rounded-md border transition-colors capitalize ${
              selectedType === type
                ? 'bg-zinc-100 text-zinc-950 font-semibold border-zinc-100'
                : 'bg-zinc-950 text-zinc-400 border-zinc-800 hover:text-zinc-200'
            }`}
          >
            {type.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Loading & Error States */}
      {loading && (
        <div className="text-center py-12 text-xs font-mono text-zinc-500">
          Loading structured knowledge records...
        </div>
      )}

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-xs font-mono text-red-400 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Extracted Knowledge Grid */}
      {!loading && !error && (
        <div>
          {items.length === 0 ? (
            <div className="text-center py-16 bg-zinc-950 border border-zinc-800/80 rounded-xl">
              <Cpu className="w-8 h-8 text-zinc-600 mx-auto mb-2" />
              <p className="text-xs text-zinc-400 font-mono font-medium">No structured information records found in SQLite database.</p>
              <p className="text-[11px] text-zinc-600 font-mono mt-1">Upload a document to extract dynamic entities, normalized values, and save to the knowledge store.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {items.map((item) => (
                <div
                  key={item.id}
                  onClick={() => onSelectDocument(item.id)}
                  className="bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-xl p-4 transition-all cursor-pointer group flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] px-2 py-0.5 rounded font-mono uppercase bg-zinc-900 border border-zinc-800 text-zinc-300 font-semibold">
                        {item.document_type.replace('_', ' ')}
                      </span>
                      <span className="text-[10px] font-mono text-zinc-500">{item.created_at}</span>
                    </div>

                    <h3 className="text-xs font-mono font-semibold text-zinc-100 leading-snug mb-3 group-hover:text-white">
                      {item.title_highlight}
                    </h3>

                    {/* Key Highlights Entity Pills */}
                    {item.key_highlights && Object.keys(item.key_highlights).length > 0 && (
                      <div className="space-y-1 mb-3 bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/60">
                        {Object.entries(item.key_highlights).slice(0, 3).map(([k, v], idx) => (
                          <div key={idx} className="flex items-center justify-between text-[11px] font-mono">
                            <span className="text-zinc-500 capitalize">{k.replace('_', ' ')}:</span>
                            <span className="text-zinc-200 font-medium truncate max-w-[140px]">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-2 bg-zinc-900/40 p-2 rounded-lg border border-zinc-800/40 text-center font-mono text-[11px] mb-3">
                      <div>
                        <span className="text-[9px] text-zinc-500 uppercase block">Extracted Fields</span>
                        <span className="text-zinc-200 font-semibold">{item.entity_count}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-zinc-500 uppercase block">Tables</span>
                        <span className="text-zinc-200 font-semibold">{item.table_count}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-zinc-800/80 text-xs font-mono">
                    <span className="text-zinc-400 text-[11px] flex items-center space-x-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>Conf: {item.average_confidence}%</span>
                    </span>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={(e) => handleDelete(item.id, item.title_highlight, e)}
                        className="p-1 text-zinc-500 hover:text-red-400 transition-colors"
                        title="Delete Record"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        className="flex items-center space-x-1 text-zinc-200 hover:text-white font-medium text-[11px]"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect JSON</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
