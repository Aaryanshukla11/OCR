import React, { useEffect, useState } from 'react';
import { Folder, Play } from 'lucide-react';
import type { CategoryData } from '../types';

interface CategoryBrowserProps {
  onSelectSampleFile: (category: string, filename: string) => void;
}

export const CategoryBrowser: React.FC<CategoryBrowserProps> = ({ onSelectSampleFile }) => {
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/test-data')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.categories) {
          setCategories(data.categories);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load test data categories:', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <Folder className="w-4 h-4 text-indigo-400" />
          <span>Local Evaluation Dataset Categories (13 Test Benchmark Sets)</span>
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Select any pre-configured document sample from these categories to run an instant PaddleOCR evaluation.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-xs text-slate-500">
          Loading test categories...
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {categories.map((cat) => (
            <div
              key={cat.category}
              className="bg-slate-950 p-4 rounded-xl border border-slate-800/90 hover:border-indigo-500/40 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <span className="w-6 h-6 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs font-mono font-bold">
                    {cat.category.split('-')[0]}
                  </span>
                  <h3 className="text-xs font-bold text-slate-200 uppercase font-mono tracking-tight">
                    {cat.category.split('-').slice(1).join(' ')}
                  </h3>
                </div>

                <div className="space-y-1.5 mt-3">
                  {cat.files.length === 0 ? (
                    <span className="text-[11px] text-slate-600 italic">No files in category</span>
                  ) : (
                    cat.files.map((file) => (
                      <button
                        key={file}
                        onClick={() => onSelectSampleFile(cat.category, file)}
                        className="w-full text-left p-2 bg-slate-900 hover:bg-indigo-600/20 hover:border-indigo-500/40 border border-slate-800 rounded text-xs font-mono text-slate-300 flex items-center justify-between group transition-all"
                      >
                        <span className="truncate pr-2">{file}</span>
                        <Play className="w-3 h-3 text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                      </button>
                    ))
                  )}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60 text-[10px] text-slate-500 font-mono flex items-center justify-between">
                <span>{cat.files.length} sample(s)</span>
                <span className="text-slate-400">GT Included</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
