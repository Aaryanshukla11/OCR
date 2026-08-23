import React, { useState, useEffect } from 'react';
import { 
  FileSpreadsheet, Copy, Download, FileJson, Database, Upload, 
  Eye, X, Search, Check, ExternalLink, Cpu
} from 'lucide-react';
import type { OCRResponse, ExtractedEntity, ExtractedTable, StructuredInformationSummary } from '../types';

interface StructuredDataStoreProps {
  ocrData?: OCRResponse | null;
  onUploadClick?: () => void;
  onSelectDocument: (docId: string) => void;
}

export const StructuredDataStore: React.FC<StructuredDataStoreProps> = ({
  ocrData = null,
  onUploadClick = () => {},
  onSelectDocument,
}) => {
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showJsonModal, setShowJsonModal] = useState(false);
  const [selectedFieldSource, setSelectedFieldSource] = useState<ExtractedEntity | null>(null);
  
  const [historyItems, setHistoryItems] = useState<StructuredInformationSummary[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [copyNotice, setCopyNotice] = useState<string | null>(null);

  const intel = ocrData?.intelligence;
  const filename = ocrData?.filename || 'Uploaded Document';
  const docType = intel?.document_type || 'unknown';
  const confidence = Math.round((intel?.confidence_score || ocrData?.average_confidence || 0.95) * 100);
  const entities: ExtractedEntity[] = intel?.entities || [];
  const tables: ExtractedTable[] = intel?.tables || [];

  // Fetch SQLite document history when modal is opened
  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const params = new URLSearchParams();
      if (historySearch.trim()) params.append('search', historySearch.trim());
      const res = await fetch(`http://localhost:8000/api/documents?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to fetch document history');
      const data = await res.json();
      setHistoryItems(data.documents || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (showHistoryModal) {
      fetchHistory();
    }
  }, [showHistoryModal, historySearch]);

  const triggerCopyNotice = (msg: string) => {
    setCopyNotice(msg);
    setTimeout(() => setCopyNotice(null), 2500);
  };

  const handleCopyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    triggerCopyNotice(`Copied ${label}: "${text}"`);
  };

  const handleCopyEntireTable = () => {
    if (!ocrData || entities.length === 0) return;

    let text = `FIELD\tVALUE\tTYPE\tVALIDATION STATUS\tCONFIDENCE\n`;
    entities.forEach(e => {
      text += `${e.label || e.key}\t${e.normalized_value ?? e.raw_value}\t${e.value_type}\t${e.validation_status || 'VALIDATED'}\t${Math.round(e.confidence * 100)}%\n`;
    });

    if (tables.length > 0) {
      tables.forEach((t, tIdx) => {
        text += `\n--- TABLE ${tIdx + 1} ---\n`;
        if (t.headers?.length) text += `${t.headers.join('\t')}\n`;
        t.rows.forEach(r => {
          text += `${r.join('\t')}\n`;
        });
      });
    }

    navigator.clipboard.writeText(text);
    triggerCopyNotice('Copied entire spreadsheet table to clipboard!');
  };

  const handleDownloadCSV = () => {
    if (!ocrData) return;

    let csvContent = `FIELD,VALUE,TYPE,VALIDATION STATUS,CONFIDENCE\n`;
    entities.forEach(e => {
      const val = String(e.normalized_value ?? e.raw_value).replace(/"/g, '""');
      const label = String(e.label || e.key).replace(/"/g, '""');
      csvContent += `"${label}","${val}","${e.value_type}","${e.validation_status || 'VALIDATED'}","${Math.round(e.confidence * 100)}%"\n`;
    });

    if (tables.length > 0) {
      tables.forEach((t, tIdx) => {
        csvContent += `\n"--- TABLE ${tIdx + 1} ---"\n`;
        if (t.headers?.length) {
          csvContent += t.headers.map(h => `"${String(h).replace(/"/g, '""')}"`).join(',') + '\n';
        }
        t.rows.forEach(r => {
          csvContent += r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',') + '\n';
        });
      });
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename.replace(/\.[^/.]+$/, '')}_extracted_data.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadExcel = () => {
    if (!ocrData) return;

    // Build multi-sheet SpreadsheetML XML for native Excel rendering
    let xml = `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
 <Styles>
  <Style ss:ID="Header"><Font ss:Bold="1" ss:Color="#FFFFFF"/><Interior ss:Color="#18181B" ss:Pattern="Solid"/></Style>
  <Style ss:ID="Title"><Font ss:Size="14" ss:Bold="1" ss:Color="#18181B"/></Style>
 </Styles>
 <Worksheet ss:Name="Extracted Fields">
  <Table>
   <Row ss:StyleID="Header">
    <Cell><Data ss:Type="String">Field Name</Data></Cell>
    <Cell><Data ss:Type="String">Extracted Value</Data></Cell>
    <Cell><Data ss:Type="String">Value Type</Data></Cell>
    <Cell><Data ss:Type="String">Validation Status</Data></Cell>
    <Cell><Data ss:Type="String">Confidence</Data></Cell>
   </Row>\n`;

    entities.forEach(e => {
      const label = e.label || e.key;
      const val = String(e.normalized_value ?? e.raw_value);
      xml += `   <Row>
    <Cell><Data ss:Type="String">${escapeXml(label)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(val)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(e.value_type)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(e.validation_status || 'VALIDATED')}</Data></Cell>
    <Cell><Data ss:Type="String">${Math.round(e.confidence * 100)}%</Data></Cell>
   </Row>\n`;
    });

    xml += `  </Table>
 </Worksheet>\n`;

    // Add extra worksheets if document contains line item tables
    tables.forEach((t, tIdx) => {
      xml += ` <Worksheet ss:Name="Table ${tIdx + 1}">
  <Table>\n`;
      if (t.headers?.length) {
        xml += `   <Row ss:StyleID="Header">\n`;
        t.headers.forEach(h => {
          xml += `    <Cell><Data ss:Type="String">${escapeXml(h)}</Data></Cell>\n`;
        });
        xml += `   </Row>\n`;
      }
      t.rows.forEach(r => {
        xml += `   <Row>\n`;
        r.forEach(c => {
          xml += `    <Cell><Data ss:Type="String">${escapeXml(String(c))}</Data></Cell>\n`;
        });
        xml += `   </Row>\n`;
      });
      xml += `  </Table>
 </Worksheet>\n`;
    });

    xml += `</Workbook>`;

    const blob = new Blob([xml], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename.replace(/\.[^/.]+$/, '')}_spreadsheet.xls`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownloadJSON = () => {
    if (!ocrData) return;
    const jsonStr = JSON.stringify(intel?.structured_json || ocrData, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename.replace(/\.[^/.]+$/, '')}_structured.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  function escapeXml(unsafe: string) {
    return unsafe.replace(/[<>&'"]/g, c => {
      switch (c) {
        case '<': return '&lt;';
        case '>': return '&gt;';
        case '&': return '&amp;';
        case '\'': return '&apos;';
        case '"': return '&quot;';
        default: return c;
      }
    });
  }

  // --- EMPTY STATE WHEN NO DOCUMENT IS LOADED ---
  if (!ocrData) {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 space-y-6">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-2xl p-12 text-center shadow-xs">
          <div className="w-16 h-16 bg-zinc-950 border border-zinc-800 rounded-2xl flex items-center justify-center mx-auto mb-4 text-zinc-400">
            <FileSpreadsheet className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-bold font-mono text-zinc-100 mb-1">No document selected</h2>
          <p className="text-xs text-zinc-400 font-mono max-w-md mx-auto mb-6">
            Upload a document to view extracted dynamic fields and line items into an Excel-style spreadsheet data table.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={onUploadClick}
              className="bg-zinc-100 text-zinc-950 font-bold px-5 py-2.5 rounded-xl text-xs font-mono hover:bg-white transition-all shadow-xs flex items-center space-x-2"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Document</span>
            </button>

            <button
              onClick={() => setShowHistoryModal(true)}
              className="bg-zinc-950 text-zinc-300 border border-zinc-800 font-semibold px-5 py-2.5 rounded-xl text-xs font-mono hover:bg-zinc-900 hover:text-white transition-all flex items-center space-x-2"
            >
              <Database className="w-4 h-4 text-zinc-400" />
              <span>Select from Document History</span>
            </button>
          </div>
        </div>

        {/* History Modal when opened in empty state */}
        {showHistoryModal && renderHistoryModal()}
      </div>
    );
  }

  // --- MAIN CURRENT DOCUMENT SPREADSHEET VIEW ---
  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Toast Notification */}
      {copyNotice && (
        <div className="fixed top-4 right-4 z-50 bg-zinc-100 text-zinc-950 border border-zinc-300 font-mono text-xs px-4 py-2.5 rounded-xl shadow-lg flex items-center space-x-2 animate-bounce">
          <Check className="w-4 h-4 text-emerald-600" />
          <span className="font-semibold">{copyNotice}</span>
        </div>
      )}

      {/* CURRENT DOCUMENT HEADER */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-emerald-400 px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
              CURRENT DOCUMENT
            </span>
            <span className="text-[10px] font-mono text-zinc-500">• Status: Completed</span>
          </div>

          <h2 className="text-base font-bold font-mono text-zinc-100 flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-zinc-400" />
            <span>{filename}</span>
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
          <span className="px-2.5 py-1 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-300 font-semibold uppercase">
            Type: {docType.replace('_', ' ')}
          </span>

          <span className="px-2.5 py-1 rounded-lg bg-zinc-950 border border-zinc-800 text-emerald-400 font-medium">
            Conf: {confidence}%
          </span>

          <button
            onClick={() => setShowHistoryModal(true)}
            className="bg-zinc-950 hover:bg-zinc-900 text-zinc-300 border border-zinc-800 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center space-x-1.5"
          >
            <Database className="w-3.5 h-3.5 text-zinc-400" />
            <span>Document History</span>
          </button>
        </div>
      </div>

      {/* SPREADSHEET TOOLBAR & ACTIONS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-zinc-950 p-2.5 rounded-xl border border-zinc-800 font-mono text-xs">
        <div className="flex items-center space-x-2">
          <span className="text-zinc-400 font-semibold px-2">
            Extracted Fields: <strong className="text-zinc-100">{entities.length}</strong>
          </span>
          {tables.length > 0 && (
            <span className="text-zinc-400 font-semibold border-l border-zinc-800 pl-2">
              Extracted Tables: <strong className="text-zinc-100">{tables.length}</strong>
            </span>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={handleCopyEntireTable}
            className="bg-zinc-900 hover:bg-zinc-800 text-zinc-200 px-3 py-1.5 rounded-lg border border-zinc-800 transition-colors flex items-center space-x-1.5"
            title="Copy all tabular data to clipboard"
          >
            <Copy className="w-3.5 h-3.5 text-zinc-400" />
            <span>Copy Table</span>
          </button>

          <button
            onClick={handleDownloadCSV}
            className="bg-zinc-900 hover:bg-zinc-800 text-zinc-200 px-3 py-1.5 rounded-lg border border-zinc-800 transition-colors flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5 text-zinc-400" />
            <span>CSV</span>
          </button>

          <button
            onClick={handleDownloadExcel}
            className="bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-500/30 px-3 py-1.5 rounded-lg transition-colors flex items-center space-x-1.5 font-bold"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Excel (.xls)</span>
          </button>

          <button
            onClick={handleDownloadJSON}
            className="bg-zinc-900 hover:bg-zinc-800 text-zinc-200 px-3 py-1.5 rounded-lg border border-zinc-800 transition-colors flex items-center space-x-1.5"
          >
            <Download className="w-3.5 h-3.5 text-zinc-400" />
            <span>JSON</span>
          </button>

          <button
            onClick={() => setShowJsonModal(true)}
            className="bg-zinc-100 hover:bg-white text-zinc-950 font-bold px-3 py-1.5 rounded-lg transition-colors flex items-center space-x-1.5"
          >
            <FileJson className="w-3.5 h-3.5" />
            <span>View JSON</span>
          </button>
        </div>
      </div>

      {/* MAIN EXCEL-LIKE SPREADSHEET TABLE 1: EXTRACTED FIELDS */}
      <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden shadow-xs">
        <div className="p-3 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between font-mono text-xs">
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
            <span className="font-bold text-zinc-200 uppercase tracking-wider text-[11px]">
              Extracted Dynamic Fields & Normalized Values
            </span>
          </div>
          <span className="text-[10px] text-zinc-500">Excel / Spreadsheet View</span>
        </div>

        {entities.length === 0 ? (
          <div className="text-center py-12 font-mono text-xs text-zinc-500">
            No dynamic fields extracted for this document.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-zinc-950 border-b border-zinc-800 text-[10px] uppercase text-zinc-400 font-semibold tracking-wider select-none">
                  <th className="py-2.5 px-3 border-r border-zinc-800/80 w-12 text-center">#</th>
                  <th className="py-2.5 px-4 border-r border-zinc-800/80 min-w-[160px]">Field</th>
                  <th className="py-2.5 px-4 border-r border-zinc-800/80 min-w-[220px]">Extracted Data</th>
                  <th className="py-2.5 px-3 border-r border-zinc-800/80 min-w-[180px]">Identified As</th>
                  <th className="py-2.5 px-3 border-r border-zinc-800/80 min-w-[90px] text-center">Confidence</th>
                  <th className="py-2.5 px-3 text-center min-w-[90px]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 bg-zinc-950/40">
                {entities.map((e, idx) => {
                  const valStr = String(e.normalized_value ?? e.raw_value);
                  const identifiedLabel = e.identified_as ? e.identified_as.replace(/_/g, ' ').toUpperCase() : (e.value_type || 'TEXT');
                  const confPct = Math.round((e.semantic_confidence ?? e.confidence ?? 0.95) * 100);

                  return (
                    <tr 
                      key={idx}
                      className="hover:bg-zinc-900/60 transition-colors group"
                    >
                      <td className="py-2 px-3 border-r border-zinc-800/60 text-center text-zinc-500 text-[11px] select-none font-mono">
                        {idx + 1}
                      </td>

                      <td className="py-2 px-4 border-r border-zinc-800/60 font-semibold text-zinc-200">
                        <span 
                          onClick={() => handleCopyText(e.label || e.key, 'Field')}
                          className="cursor-pointer hover:underline hover:text-white"
                          title="Click to copy field name"
                        >
                          {e.label || e.key}
                        </span>
                      </td>

                      <td className="py-2 px-4 border-r border-zinc-800/60 text-zinc-100 select-text font-medium">
                        <span 
                          onClick={() => handleCopyText(valStr, e.label || e.key)}
                          className="cursor-pointer hover:text-emerald-300 font-mono break-all"
                          title="Click to copy value"
                        >
                          {valStr} {e.currency ? <strong className="text-emerald-400 font-bold ml-1">{e.currency}</strong> : ''}
                        </span>
                      </td>

                      <td className="py-2 px-3 border-r border-zinc-800/60 text-[11px]">
                        <span className="px-2 py-0.5 rounded font-mono font-bold bg-zinc-900 border border-zinc-800 text-emerald-400">
                          {identifiedLabel}
                        </span>
                      </td>

                      <td className="py-2 px-3 border-r border-zinc-800/60 text-center text-zinc-300 text-[11px] font-bold">
                        {confPct}%
                      </td>

                      <td className="py-2 px-3 text-center">
                        <div className="flex items-center justify-center space-x-1">
                          <button
                            onClick={() => handleCopyText(valStr, e.label || e.key)}
                            className="p-1 text-zinc-400 hover:text-white transition-colors"
                            title="Copy Cell Value"
                          >
                            <Copy className="w-3.5 h-3.5" />
                          </button>

                          {e.source && (
                            <button
                              onClick={() => setSelectedFieldSource(e)}
                              className="p-1 text-zinc-400 hover:text-emerald-400 transition-colors"
                              title="View OCR Provenance & Source"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* EXTRACTED TABLES SECTION (LINE ITEMS & TABULAR DATA) */}
      {tables.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-bold font-mono text-zinc-100 flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>EXTRACTED LINE-ITEM TABLES ({tables.length})</span>
          </h3>

          {tables.map((tbl, tIdx) => (
            <div key={tIdx} className="bg-zinc-900/60 border border-zinc-800 rounded-xl overflow-hidden shadow-xs">
              <div className="p-3 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between font-mono text-xs">
                <span className="font-bold text-zinc-200">Table {tIdx + 1} (Page {tbl.page_number})</span>
                <span className="text-[10px] text-zinc-500">Rows: {tbl.rows.length}</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left font-mono text-xs border-collapse">
                  {tbl.headers?.length > 0 && (
                    <thead>
                      <tr className="bg-zinc-950 border-b border-zinc-800 text-[10px] uppercase text-zinc-400 font-semibold tracking-wider">
                        {tbl.headers.map((h, hIdx) => (
                          <th key={hIdx} className="py-2.5 px-4 border-r border-zinc-800/80">{h}</th>
                        ))}
                      </tr>
                    </thead>
                  )}
                  <tbody className="divide-y divide-zinc-800/60 bg-zinc-950/40">
                    {tbl.rows.map((r, rIdx) => (
                      <tr key={rIdx} className="hover:bg-zinc-900/60 transition-colors">
                        {r.map((c, cIdx) => (
                          <td 
                            key={cIdx} 
                            onClick={() => handleCopyText(String(c), `Cell (${rIdx+1}, ${cIdx+1})`)}
                            className="py-2 px-4 border-r border-zinc-800/60 text-zinc-200 select-text cursor-pointer hover:text-white"
                          >
                            {String(c)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PROVENANCE / SOURCE MODAL */}
      {selectedFieldSource && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-lg w-full p-6 space-y-4 font-mono shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="text-sm font-bold text-zinc-100 flex items-center space-x-2">
                <ExternalLink className="w-4 h-4 text-emerald-400" />
                <span>OCR Provenance & Source Information</span>
              </h3>
              <button onClick={() => setSelectedFieldSource(null)} className="text-zinc-500 hover:text-zinc-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-zinc-500 uppercase text-[10px] block">Field Label</span>
                <span className="text-zinc-100 font-bold text-sm">{selectedFieldSource.label || selectedFieldSource.key}</span>
              </div>

              <div>
                <span className="text-zinc-500 uppercase text-[10px] block">Extracted Normalized Value</span>
                <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800 text-emerald-300 font-bold break-all mt-1">
                  {String(selectedFieldSource.normalized_value ?? selectedFieldSource.raw_value)}
                </div>
              </div>

              <div>
                <span className="text-zinc-500 uppercase text-[10px] block">Source OCR Text</span>
                <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800 text-zinc-200 break-all mt-1">
                  {selectedFieldSource.source?.text || selectedFieldSource.raw_value}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="bg-zinc-950 p-2 rounded-lg border border-zinc-800">
                  <span className="text-zinc-500 block text-[9px] uppercase">Page Number</span>
                  <span className="text-zinc-200 font-semibold">Page {selectedFieldSource.source?.page || 1}</span>
                </div>

                <div className="bg-zinc-950 p-2 rounded-lg border border-zinc-800">
                  <span className="text-zinc-500 block text-[9px] uppercase">Bounding Box BBox</span>
                  <span className="text-zinc-200 font-semibold text-[10px]">
                    {JSON.stringify(selectedFieldSource.source?.bbox || [])}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedFieldSource(null)}
                className="bg-zinc-100 text-zinc-950 font-bold px-4 py-1.5 rounded-lg text-xs hover:bg-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* RAW JSON VIEW MODAL */}
      {showJsonModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-3xl w-full p-6 space-y-4 font-mono shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="text-sm font-bold text-zinc-100 flex items-center space-x-2">
                <FileJson className="w-4 h-4 text-emerald-400" />
                <span>Extracted Structured JSON Tree</span>
              </h3>
              <button onClick={() => setShowJsonModal(false)} className="text-zinc-500 hover:text-zinc-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto bg-zinc-950 p-4 rounded-xl border border-zinc-800 text-xs text-emerald-400">
              <pre className="whitespace-pre-wrap break-all">
                {JSON.stringify(intel?.structured_json || ocrData, null, 2)}
              </pre>
            </div>

            <div className="flex justify-between items-center pt-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(intel?.structured_json || ocrData, null, 2));
                  triggerCopyNotice('Copied JSON payload to clipboard!');
                }}
                className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>Copy JSON</span>
              </button>

              <button
                onClick={() => setShowJsonModal(false)}
                className="bg-zinc-100 text-zinc-950 font-bold px-4 py-1.5 rounded-lg text-xs hover:bg-white"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* DOCUMENT HISTORY MODAL */}
      {showHistoryModal && renderHistoryModal()}
    </div>
  );

  function renderHistoryModal() {
    return (
      <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl max-w-4xl w-full p-6 space-y-4 font-mono shadow-2xl max-h-[85vh] flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
            <div>
              <h3 className="text-sm font-bold text-zinc-100 flex items-center space-x-2">
                <Database className="w-4 h-4 text-zinc-400" />
                <span>SQLite Stored Document History</span>
              </h3>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                Select any previously processed document to set it as the active CURRENT DOCUMENT.
              </p>
            </div>
            <button onClick={() => setShowHistoryModal(false)} className="text-zinc-500 hover:text-zinc-200">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Search Input */}
          <div className="relative">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={historySearch}
              onChange={(e) => setHistorySearch(e.target.value)}
              placeholder="Search historical document records..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-zinc-600 font-mono"
            />
          </div>

          <div className="flex-1 overflow-y-auto pr-1">
            {loadingHistory ? (
              <div className="text-center py-12 text-xs text-zinc-500">Loading stored document history...</div>
            ) : historyItems.length === 0 ? (
              <div className="text-center py-12 text-xs text-zinc-500">No document records found in SQLite.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {historyItems.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      onSelectDocument(item.id);
                      setShowHistoryModal(false);
                    }}
                    className="p-3.5 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 rounded-xl transition-all cursor-pointer group flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] px-2 py-0.5 rounded font-mono uppercase bg-zinc-900 border border-zinc-800 text-zinc-300 font-semibold">
                          {item.document_type.replace('_', ' ')}
                        </span>
                        <span className="text-[10px] text-zinc-500">{item.created_at}</span>
                      </div>
                      <h4 className="text-xs font-bold text-zinc-200 group-hover:text-white truncate">
                        {item.title_highlight}
                      </h4>
                    </div>

                    <div className="flex items-center justify-between pt-2 mt-2 border-t border-zinc-800/60 text-[10px] text-zinc-400">
                      <span>Fields: {item.entity_count}</span>
                      <span className="text-emerald-400 font-semibold flex items-center space-x-1">
                        <Eye className="w-3 h-3" />
                        <span>Select Document</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={() => setShowHistoryModal(false)}
              className="bg-zinc-100 text-zinc-950 font-bold px-4 py-1.5 rounded-lg text-xs hover:bg-white"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }
};
