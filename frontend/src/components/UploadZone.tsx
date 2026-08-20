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
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 shadow-xs">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider flex items-center space-x-2 font-mono">
          <UploadCloud className="w-4 h-4 text-zinc-400" />
          <span>Document & Image Upload</span>
        </h2>
        <button
          onClick={() => setShowGtInput(!showGtInput)}
          className={`text-xs px-2.5 py-1 rounded-md border transition-colors flex items-center space-x-1 ${
            showGtInput || groundTruthText
              ? 'bg-zinc-800 text-zinc-200 border-zinc-700'
              : 'bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200'
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
        className={`border border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-zinc-500 bg-zinc-900/80'
            : selectedFile
            ? 'border-zinc-700 bg-zinc-900/60'
            : 'border-zinc-800 bg-zinc-950/40 hover:border-zinc-700 hover:bg-zinc-900/40'
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
            <div className="w-10 h-10 rounded-md bg-zinc-900 text-zinc-200 border border-zinc-800 flex items-center justify-center mb-3">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <p className="text-sm font-medium text-zinc-100 mb-1">{selectedFile.name}</p>
            <div className="flex items-center space-x-3 text-xs text-zinc-400 font-mono">
              <span>Size: {formatFileSize(selectedFile.size)}</span>
              <span>•</span>
              <span className="uppercase text-zinc-300">{selectedFile.name.split('.').pop()}</span>
              {selectedFile.type.includes('pdf') && (
                <>
                  <span>•</span>
                  <span className="flex items-center text-zinc-300">
                    <Layers className="w-3 h-3 mr-1" /> PDF Document
                  </span>
                </>
              )}
            </div>
            <p className="text-xs text-zinc-400 mt-3 hover:underline">Click or drop to replace file</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 rounded-md bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 mb-3">
              <UploadCloud className="w-5 h-5 text-zinc-300" />
            </div>
            <p className="text-sm font-medium text-zinc-200 mb-1">
              Drop document or image file here, or <span className="text-zinc-100 underline underline-offset-2">Browse Files</span>
            </p>
            <p className="text-xs text-zinc-500 mt-2 font-mono">
              PNG • JPG • JPEG • WEBP • PDF
            </p>
          </div>
        )}
      </div>

      {/* Ground Truth Drawer */}
      {(showGtInput || groundTruthText) && (
        <div className="mt-4 p-3 bg-zinc-950 border border-zinc-800 rounded-lg">
          <label className="block text-xs font-medium text-zinc-400 mb-1.5 flex items-center justify-between">
            <span>Ground Truth Reference Text (For CER / WER Accuracy Evaluation)</span>
            {groundTruthText && (
              <button
                onClick={() => setGroundTruthText('')}
                className="text-[10px] text-zinc-400 hover:text-zinc-200 hover:underline"
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
            className="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-zinc-700 font-mono"
          />
        </div>
      )}

      {/* Action Button */}
      <div className="mt-4 flex justify-end">
        <button
          disabled={!selectedFile || isLoading}
          onClick={() => selectedFile && onFileSelect(selectedFile, groundTruthText)}
          className={`w-full sm:w-auto px-5 py-2 rounded-md text-xs font-semibold flex items-center justify-center space-x-2 transition-colors ${
            !selectedFile || isLoading
              ? 'bg-zinc-900 text-zinc-600 cursor-not-allowed border border-zinc-800'
              : 'bg-zinc-100 text-zinc-950 hover:bg-zinc-200 border border-zinc-200'
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-zinc-950/30 border-t-zinc-950 rounded-full animate-spin" />
              <span>Processing OCR...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-zinc-950" />
              <span>Run OCR</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

