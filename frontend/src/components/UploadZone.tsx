import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, Play, FileCode, Layers } from 'lucide-react';

interface UploadZoneProps {
  onFileSelect: (file: File, groundTruth?: string) => void;
  isLoading: boolean;
  selectedFile: File | null;
  groundTruthText: string;
  setGroundTruthText: (text: string) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFileSelect,
  isLoading,
  selectedFile,
  groundTruthText,
  setGroundTruthText,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [showGtInput, setShowGtInput] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const allowed = ['.png', '.jpg', '.jpeg', '.webp', '.pdf'];
    if (!allowed.includes(ext)) {
      alert(`File type ${ext} is not supported. Please upload PNG, JPG, JPEG, WEBP, or PDF.`);
      return;
    }
    onFileSelect(file, groundTruthText);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
          <UploadCloud className="w-4 h-4 text-indigo-400" />
          <span>Document & Image Upload</span>
        </h2>
        <button
          onClick={() => setShowGtInput(!showGtInput)}
          className={`text-xs px-2.5 py-1 rounded border transition-colors flex items-center space-x-1 ${
            showGtInput || groundTruthText
              ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40'
              : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
          }`}
        >
          <FileCode className="w-3.5 h-3.5" />
          <span>{groundTruthText ? 'Ground Truth Attached' : '+ Ground Truth (Optional)'}</span>
        </button>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10'
            : selectedFile
            ? 'border-emerald-500/50 bg-emerald-500/5'
            : 'border-slate-800 bg-slate-950/60 hover:border-indigo-500/50 hover:bg-slate-950'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.webp,.pdf"
          onChange={handleFileChange}
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mb-3">
              <CheckCircle className="w-6 h-6" />
            </div>
            <p className="text-sm font-semibold text-slate-100 mb-1">{selectedFile.name}</p>
            <div className="flex items-center space-x-3 text-xs text-slate-400">
              <span>Size: {formatFileSize(selectedFile.size)}</span>
              <span>•</span>
              <span className="uppercase font-mono text-indigo-400">{selectedFile.name.split('.').pop()}</span>
              {selectedFile.type.includes('pdf') && (
                <>
                  <span>•</span>
                  <span className="flex items-center text-amber-400">
                    <Layers className="w-3 h-3 mr-1" /> PDF Document
                  </span>
                </>
              )}
            </div>
            <p className="text-xs text-indigo-400 mt-3 hover:underline">Click or drop to replace file</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-14 h-14 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 mb-4 group-hover:text-indigo-400">
              <UploadCloud className="w-7 h-7 text-indigo-400" />
            </div>
            <p className="text-sm font-medium text-slate-200 mb-1">
              Drop document or image file here, or <span className="text-indigo-400 underline">Browse Files</span>
            </p>
            <p className="text-xs text-slate-400 mt-2">
              Supported Formats: <strong className="text-slate-300">PNG • JPG • JPEG • WEBP • PDF</strong>
            </p>
          </div>
        )}
      </div>

      {/* Ground Truth Drawer */}
      {(showGtInput || groundTruthText) && (
        <div className="mt-4 p-3 bg-slate-950 border border-slate-800 rounded-lg">
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
            <span>Ground Truth Reference Text (For CER / WER Accuracy Evaluation)</span>
            {groundTruthText && (
              <button
                onClick={() => setGroundTruthText('')}
                className="text-[10px] text-rose-400 hover:underline"
              >
                Clear GT
              </button>
            )}
          </label>
          <textarea
            value={groundTruthText}
            onChange={(e) => setGroundTruthText(e.target.value)}
            placeholder="Paste expected exact text content here to compare PaddleOCR extraction against ground truth..."
            rows={3}
            className="w-full bg-slate-900 border border-slate-800 rounded p-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>
      )}

      {/* Action Button */}
      <div className="mt-5 flex justify-end">
        <button
          disabled={!selectedFile || isLoading}
          onClick={() => selectedFile && onFileSelect(selectedFile, groundTruthText)}
          className={`w-full sm:w-auto px-6 py-2.5 rounded-lg text-sm font-bold flex items-center justify-center space-x-2 transition-all ${
            !selectedFile || isLoading
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
              : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Running PaddleOCR...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Run OCR</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
