import type { OCRResponse, KeyValueLink } from '../types';
import { Eye, Layers, Link2, ArrowRight } from 'lucide-react';

interface DebugViewPanelProps {
  data: OCRResponse;
  activePageIndex: number;
  showOcrBoxes: boolean;
  setShowOcrBoxes: (v: boolean) => void;
  showGroupedLines: boolean;
  setShowGroupedLines: (v: boolean) => void;
  showKeyValueLinks: boolean;
  setShowKeyValueLinks: (v: boolean) => void;
  showLayoutRegions: boolean;
  setShowLayoutRegions: (v: boolean) => void;
  showReadingOrder: boolean;
  setShowReadingOrder: (v: boolean) => void;
}

export function DebugViewPanel({
  data,
  activePageIndex,
  showOcrBoxes,
  setShowOcrBoxes,
  showGroupedLines,
  setShowGroupedLines,
  showKeyValueLinks,
  setShowKeyValueLinks,
  showLayoutRegions,
  setShowLayoutRegions,
  showReadingOrder,
  setShowReadingOrder,
}: DebugViewPanelProps) {
  const interDoc = data.intermediate_representation;
  const currentPageInter = interDoc?.pages[activePageIndex] || interDoc?.pages[0];
  const relationships: KeyValueLink[] = currentPageInter?.relationships || [];

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 space-y-4 shadow-sm font-mono text-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center space-x-2">
          <Eye className="w-4 h-4 text-emerald-400" />
          <span className="font-bold text-zinc-100 uppercase tracking-wider">
            Intermediate Layer Debug Inspector
          </span>
        </div>
        <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded font-semibold">
          ACTIVE
        </span>
      </div>

      {/* Confidence Metrics Breakdown */}
      {interDoc && (
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800">
            <div className="text-[10px] text-zinc-400">OCR Confidence</div>
            <div className="text-sm font-bold text-cyan-400 mt-0.5">{interDoc.ocr_confidence}%</div>
          </div>
          <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800">
            <div className="text-[10px] text-zinc-400">Grouping Conf</div>
            <div className="text-sm font-bold text-purple-400 mt-0.5">{interDoc.grouping_confidence}%</div>
          </div>
          <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800">
            <div className="text-[10px] text-zinc-400">Relationship Conf</div>
            <div className="text-sm font-bold text-amber-400 mt-0.5">{interDoc.relationship_confidence}%</div>
          </div>
        </div>
      )}

      {/* Layer Overlay Controls */}
      <div className="space-y-2">
        <div className="text-[11px] font-semibold text-zinc-300 flex items-center space-x-1.5">
          <Layers className="w-3.5 h-3.5 text-zinc-400" />
          <span>VISUAL OVERLAY TOGGLES</span>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <label className="flex items-center space-x-2 bg-zinc-950 p-2 rounded-lg border border-zinc-800/80 cursor-pointer hover:bg-zinc-900 transition-colors">
            <input
              type="checkbox"
              checked={showOcrBoxes}
              onChange={(e) => setShowOcrBoxes(e.target.checked)}
              className="rounded bg-zinc-800 border-zinc-700 text-cyan-500 focus:ring-0"
            />
            <span className="text-cyan-400 font-medium">1. Raw OCR Boxes</span>
          </label>

          <label className="flex items-center space-x-2 bg-zinc-950 p-2 rounded-lg border border-zinc-800/80 cursor-pointer hover:bg-zinc-900 transition-colors">
            <input
              type="checkbox"
              checked={showGroupedLines}
              onChange={(e) => setShowGroupedLines(e.target.checked)}
              className="rounded bg-zinc-800 border-zinc-700 text-purple-500 focus:ring-0"
            />
            <span className="text-purple-400 font-medium">2. Grouped Lines</span>
          </label>

          <label className="flex items-center space-x-2 bg-zinc-950 p-2 rounded-lg border border-zinc-800/80 cursor-pointer hover:bg-zinc-900 transition-colors">
            <input
              type="checkbox"
              checked={showKeyValueLinks}
              onChange={(e) => setShowKeyValueLinks(e.target.checked)}
              className="rounded bg-zinc-800 border-zinc-700 text-amber-500 focus:ring-0"
            />
            <span className="text-amber-400 font-medium">3. Key-Value Vectors</span>
          </label>

          <label className="flex items-center space-x-2 bg-zinc-950 p-2 rounded-lg border border-zinc-800/80 cursor-pointer hover:bg-zinc-900 transition-colors">
            <input
              type="checkbox"
              checked={showLayoutRegions}
              onChange={(e) => setShowLayoutRegions(e.target.checked)}
              className="rounded bg-zinc-800 border-zinc-700 text-emerald-500 focus:ring-0"
            />
            <span className="text-emerald-400 font-medium">4. Layout Regions</span>
          </label>

          <label className="flex items-center space-x-2 bg-zinc-950 p-2 rounded-lg border border-zinc-800/80 col-span-2 cursor-pointer hover:bg-zinc-900 transition-colors">
            <input
              type="checkbox"
              checked={showReadingOrder}
              onChange={(e) => setShowReadingOrder(e.target.checked)}
              className="rounded bg-zinc-800 border-zinc-700 text-blue-500 focus:ring-0"
            />
            <span className="text-blue-400 font-medium">5. Multi-Column Reading Order Badges</span>
          </label>
        </div>
      </div>

      {/* Extracted Key-Value Relationships List */}
      <div className="space-y-2 pt-2 border-t border-zinc-800">
        <div className="flex items-center justify-between">
          <span className="font-semibold text-zinc-300 flex items-center space-x-1.5">
            <Link2 className="w-3.5 h-3.5 text-amber-400" />
            <span>EXTRACTED KEY-VALUE PAIRS ({relationships.length})</span>
          </span>
        </div>

        {relationships.length === 0 ? (
          <div className="text-zinc-500 text-[11px] p-3 bg-zinc-950 rounded-lg border border-zinc-800/60 text-center">
            No spatial key-value pairs detected on this page.
          </div>
        ) : (
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {relationships.map((rel, idx) => (
              <div
                key={idx}
                className="bg-zinc-950 p-2 rounded-lg border border-zinc-800 flex items-center justify-between hover:border-amber-500/50 transition-colors"
              >
                <div className="flex items-center space-x-2 overflow-hidden">
                  <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded text-[10px] font-semibold shrink-0">
                    {rel.key_text}
                  </span>
                  <ArrowRight className="w-3 h-3 text-zinc-500 shrink-0" />
                  <span className="text-zinc-200 font-medium truncate">{rel.value_text}</span>
                </div>
                <div className="flex items-center space-x-1.5 shrink-0 ml-2">
                  <span className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded">
                    {rel.value_category}
                  </span>
                  <span className="text-[10px] text-emerald-400 font-mono font-bold">
                    {Math.round(rel.confidence * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Semantic Field Identification Debug Inspector */}
      <div className="space-y-2 pt-2 border-t border-zinc-800">
        <span className="font-semibold text-zinc-300 flex items-center space-x-1.5">
          <Eye className="w-3.5 h-3.5 text-purple-400" />
          <span>DEVELOPER SEMANTIC INSPECTION PANEL</span>
        </span>

        {(!data.intelligence?.entities || data.intelligence.entities.length === 0) ? (
          <div className="text-zinc-500 text-[11px] p-3 bg-zinc-950 rounded-lg border border-zinc-800/60 text-center">
            No semantic field classifications available.
          </div>
        ) : (
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {data.intelligence.entities.map((e, idx) => (
              <div key={idx} className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800 text-[11px] space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-amber-400 font-bold">Source: {e.label || e.key}</span>
                  <span className="text-emerald-400 font-bold">{Math.round((e.semantic_confidence ?? e.confidence) * 100)}%</span>
                </div>
                <div className="text-zinc-200 font-mono">Value: <span className="text-zinc-100 font-semibold">{e.raw_value}</span></div>
                <div className="grid grid-cols-2 gap-1 pt-1 border-t border-zinc-900 text-[10px]">
                  <div><span className="text-zinc-500">Qwen Pred:</span> <span className="text-cyan-400 font-semibold">{e.qwen_prediction || 'N/A (fallback)'}</span></div>
                  <div><span className="text-zinc-500">Final Pred:</span> <span className="text-purple-300 font-bold">{e.final_prediction || e.identified_as || 'unknown_field'}</span></div>
                </div>
                <div className="text-[10px] text-zinc-400 pt-0.5">
                  <span className="text-zinc-500">Evidence:</span> {e.evidence_details?.validation_notes?.join(' | ') || e.evidence?.join(', ') || 'deterministic-validation'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
