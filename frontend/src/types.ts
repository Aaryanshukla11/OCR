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
  full_text: string;
  extracted_text?: string;
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
  identified_as?: string;
  qwen_prediction?: string;
  final_prediction?: string;
  semantic_source?: string;
  semantic_confidence?: number;
  evidence?: string[];
  evidence_details?: Record<string, any>;
  source?: SourceProvenance;
  needs_review: boolean;
  currency?: string | null;
  validation_status?: string;
  extraction_method?: string;
}

export interface ExtractedTable {
  table_id: number;
  page_number: number;
  headers: string[];
  rows: any[][];
  bbox: number[];
  confidence: number;
}

export interface DynamicColumn {
  column_name: string;
  label: string;
  type: string;
}

export interface DynamicDataset {
  dataset_id: string;
  document_type: string;
  title: string;
  columns: DynamicColumn[];
  header_record: Record<string, any>;
  table_rows: Record<string, any>[];
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

export interface LayoutRegion {
  id: string;
  type: string; // 'header' | 'body' | 'footer' | 'table'
  bbox: number[];
  reading_order: number;
  element_ids?: string[];
}

export interface TextGroup {
  id: string;
  element_ids: string[];
  text: string;
  bbox: number[];
  confidence: number;
  line_count: number;
  region_id?: string;
}

export interface KeyValueLink {
  key_text: string;
  value_text: string;
  key_region: string;
  value_region: string;
  relationship: string;
  confidence: number;
  value_category: string;
  key_bbox: number[];
  value_bbox: number[];
  spatial_relation: string;
}

export interface IntermediatePage {
  page: number;
  width: number;
  height: number;
  regions: LayoutRegion[];
  elements: any[];
  groups: TextGroup[];
  relationships: KeyValueLink[];
  reading_order: string[];
}

export interface RelationshipGraphNode {
  id: string;
  label: string;
  type: string;
  bbox: number[];
}

export interface RelationshipGraphEdge {
  source: string;
  target: string;
  type: string;
  confidence: number;
}

export interface RelationshipGraph {
  nodes: RelationshipGraphNode[];
  edges: RelationshipGraphEdge[];
}

export interface IntermediateDocument {
  filename: string;
  total_pages: number;
  pages: IntermediatePage[];
  ocr_confidence: number;
  grouping_confidence: number;
  relationship_confidence: number;
  graph: RelationshipGraph;
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
  intermediate_representation?: IntermediateDocument;
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
