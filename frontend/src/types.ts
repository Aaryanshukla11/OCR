export interface BoundingBoxRegion {
  id: number;
  text: string;
  confidence: number;
  polygon: number[][]; // [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
  bbox: number[];       // [xmin, ymin, xmax, ymax]
}

export interface PageOCRResult {
  page_number: number;
  regions: BoundingBoxRegion[];
  extracted_text: string;
  average_confidence: number;
  page_image?: string;
}

export interface AccuracyMetrics {
  available: boolean;
  ground_truth?: string | null;
  cer?: number | null;
  wer?: number | null;
  message: string;
}

export interface SourceProvenance {
  page: number;
  bbox: number[];
  text: string;
}

export interface ExtractedEntity {
  key: string;
  label: string;
  raw_value: string;
  normalized_value?: string | number | boolean | null;
  value_type: string;
  confidence: number;
  source?: SourceProvenance;
  needs_review: boolean;
  currency?: string | null;
}

export interface ExtractedTable {
  table_id: number;
  page_number: number;
  headers: string[];
  rows: any[][];
  bbox: number[];
  confidence: number;
}

export interface DocumentIntelligenceResult {
  document_id: string;
  filename: string;
  document_type: string;
  confidence_score: number;
  entities: ExtractedEntity[];
  tables: ExtractedTable[];
  structured_json: Record<string, any>;
}

export interface OCRResponse {
  filename: string;
  file_type: string;
  total_pages: number;
  processing_time: number;
  device: string;
  average_confidence: number;
  total_regions: number;
  pages: PageOCRResult[];
  aggregated_text: string;
  accuracy: AccuracyMetrics;
  status: string;
  intelligence?: DocumentIntelligenceResult;
}

export interface StructuredInformationSummary {
  id: string;
  document_type: string;
  title_highlight: string;
  created_at: string;
  total_pages: number;
  average_confidence: number;
  entity_count: number;
  table_count: number;
  needs_review_count: number;
  key_highlights?: Record<string, any>;
}

export interface QueryPlan {
  query_text: string;
  target_document_type?: string | null;
  field_key?: string | null;
  date_start?: string | null;
  date_end?: string | null;
  search_terms: string[];
  aggregation: string;
  sql_executed: string;
}

export interface QueryResponse {
  query: string;
  plan: QueryPlan;
  answer_summary: string;
  total_matches: number;
  aggregated_value?: number | string | null;
  documents: StructuredInformationSummary[];
  matching_entities: ExtractedEntity[];
}

export interface HistoryItem {
  id: string;
  filename: string;
  timestamp: string;
  processing_time: number;
  total_regions: number;
  average_confidence: number;
  device: string;
  status: string;
  file_type: string;
  pages_count: number;
}

export interface CategoryData {
  category: string;
  files: string[];
}
