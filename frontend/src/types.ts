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
