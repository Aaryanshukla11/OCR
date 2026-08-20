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
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 shadow-xs">
      <div className="mb-5">
        <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center space-x-2 font-mono">
          <Folder className="w-4 h-4 text-zinc-400" />
          <span>Local Evaluation Dataset Categories</span>
        </h2>
        <p className="text-xs text-zinc-400 mt-1">
          Select any pre-configured document sample from these categories to run an instant PaddleOCR evaluation.
        </p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-xs text-zinc-500 font-mono">
          Loading test categories...
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {categories.map((cat) => (
            <div
              key={cat.category}
              className="bg-zinc-950 p-4 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <span className="w-5 h-5 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 flex items-center justify-center text-[10px] font-mono font-semibold">
                    {cat.category.split('-')[0]}
                  </span>
                  <h3 className="text-xs font-semibold text-zinc-200 uppercase font-mono tracking-tight">
                    {cat.category.split('-').slice(1).join(' ')}
                  </h3>
                </div>

                <div className="space-y-1.5 mt-3">
                  {cat.files.length === 0 ? (
                    <span className="text-[11px] text-zinc-600 italic">No files in category</span>
                  ) : (
                    cat.files.map((file) => (
                      <button
                        key={file}
                        onClick={() => onSelectSampleFile(cat.category, file)}
                        className="w-full text-left p-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800/80 rounded text-xs font-mono text-zinc-300 flex items-center justify-between group transition-colors"
                      >
                        <span className="truncate pr-2">{file}</span>
                        <Play className="w-3 h-3 text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                      </button>
                    ))
                  )}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-zinc-800/80 text-[10px] text-zinc-500 font-mono flex items-center justify-between">
                <span>{cat.files.length} sample(s)</span>
                <span className="text-zinc-400">GT Included</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

