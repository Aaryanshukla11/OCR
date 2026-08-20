import time
import logging
import os
import numpy as np
from typing import List, Optional

from app.core.config import AppConfig, load_config
from app.core.schemas import (
    OCRDocumentResult, DocumentInfo, PageResult, RegionResult, 
    ProcessingMetadata, AccuracyMetrics
)
from app.input.loader import ImageLoader
from app.input.pdf import PDFLoader
from app.preprocessing.preprocessor import Preprocessor
from app.postprocessing.postprocessor import Postprocessor
from app.validation.validator import InputValidator, ValidationError
from app.models.paddleocr.provider import PaddleOCRProvider
from app.services.evaluator import compute_accuracy_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("OCRPipeline")

class OCRPipeline:
    """
    Central OCR Engine Pipeline Orchestrator.
    Decouples engine orchestration logic from specific underlying OCR models.
    """
    _instance = None

    @classmethod
    def get_instance(cls, config: Optional[AppConfig] = None):
        if cls._instance is None:
            cls._instance = cls(config=config or load_config())
        return cls._instance

    def __init__(self, config: AppConfig):
        logger.info(f"Initializing {config.engine.name} v{config.engine.version}...")
        self.config = config
        
        # Instantiate pipeline layers
        self.validator = InputValidator(config.validation)
        self.preprocessor = Preprocessor(config.preprocessing)
        self.postprocessor = Postprocessor(config.postprocessing)
        
        # Select and initialize model provider based on config
        provider_type = config.ocr.provider.lower()
        if provider_type == "paddleocr":
            self.model_provider = PaddleOCRProvider.get_instance(lang=config.ocr.lang)
        else:
            logger.warning(f"Unknown provider '{provider_type}', falling back to PaddleOCRProvider.")
            self.model_provider = PaddleOCRProvider.get_instance(lang=config.ocr.lang)
            
        logger.info(f"OCRPipeline active with provider '{self.model_provider.provider_name}' on device '{self.model_provider.device}'")

    def process_file(
        self,
        file_bytes: bytes,
        filename: str,
        ground_truth: Optional[str] = None
    ) -> OCRDocumentResult:
        t0 = time.time()
        logger.info(f"OCR request received for file: '{filename}' ({len(file_bytes)} bytes)")
        
        # Step 1: Input Validation
        self.validator.validate_file_metadata(filename, len(file_bytes))
        
        ext = os.path.splitext(filename)[1].lower()
        pages_list: List[PageResult] = []
        
        if ext == ".pdf":
            logger.info(f"Rendering PDF document pages...")
            pdf_pages_data = PDFLoader.render_pdf_pages(file_bytes)
            page_count = len(pdf_pages_data)
            logger.info(f"Loaded {page_count} PDF page(s)")
            
            for page_num, raw_np_img, orig_w, orig_h in pdf_pages_data:
                self.validator.validate_image_array(raw_np_img)
                prep_img = self.preprocessor.process(raw_np_img)
                
                # Model inference via Provider Interface
                raw_regions = self.model_provider.process_image(prep_img)
                
                # Validation & Postprocessing
                sanitized = self.validator.sanitize_regions(raw_regions, orig_w, orig_h)
                final_regions_dict = self.postprocessor.process_page_regions(sanitized)
                
                region_objects = [RegionResult(**r) for r in final_regions_dict]
                page_text = "\n".join([r.text for r in region_objects])
                page_avg_conf = self.postprocessor.calculate_confidence(final_regions_dict)
                
                pages_list.append(PageResult(
                    page_number=page_num,
                    width=orig_w,
                    height=orig_h,
                    regions=region_objects,
                    full_text=page_text,
                    average_confidence=page_avg_conf
                ))
        else:
            page_count = 1
            raw_np_img, orig_w, orig_h = ImageLoader.load_from_bytes(file_bytes)
            self.validator.validate_image_array(raw_np_img)
            prep_img = self.preprocessor.process(raw_np_img)
            
            # Model inference via Provider Interface
            raw_regions = self.model_provider.process_image(prep_img)
            
            # Validation & Postprocessing
            sanitized = self.validator.sanitize_regions(raw_regions, orig_w, orig_h)
            final_regions_dict = self.postprocessor.process_page_regions(sanitized)
            
            region_objects = [RegionResult(**r) for r in final_regions_dict]
            page_text = "\n".join([r.text for r in region_objects])
            page_avg_conf = self.postprocessor.calculate_confidence(final_regions_dict)
            
            pages_list.append(PageResult(
                page_number=1,
                width=orig_w,
                height=orig_h,
                regions=region_objects,
                full_text=page_text,
                average_confidence=page_avg_conf
            ))
            
        elapsed_sec = time.time() - t0
        elapsed_ms = round(elapsed_sec * 1000, 2)
        
        # Aggregate document text & overall metrics
        aggregated_text = "\n\n--- Page Break ---\n\n".join([p.full_text for p in pages_list])
        all_region_confs = [r.confidence for p in pages_list for r in p.regions]
        
        if all_region_confs:
            doc_avg_conf = float(np.mean(all_region_confs))
            doc_avg_conf = round(doc_avg_conf * 100, 1) if doc_avg_conf <= 1.0 else round(doc_avg_conf, 1)
        else:
            doc_avg_conf = 0.0
            
        total_regions_count = sum(len(p.regions) for p in pages_list)
        
        # Step 6: Evaluation
        accuracy_dict = compute_accuracy_metrics(aggregated_text, ground_truth)
        
        logger.info(
            f"OCR pipeline completed for '{filename}': {total_regions_count} regions, "
            f"{doc_avg_conf}% avg confidence in {elapsed_ms} ms on {self.model_provider.device}"
        )
        
        return OCRDocumentResult(
            document=DocumentInfo(
                filename=filename,
                page_count=page_count,
                file_type=ext[1:].upper()
            ),
            pages=pages_list,
            processing=ProcessingMetadata(
                processing_time_ms=elapsed_ms,
                processing_time_sec=round(elapsed_sec, 2),
                device=self.model_provider.device,
                model="PaddleOCR 3.7.0",
                provider=self.model_provider.provider_name
            ),
            aggregated_text=aggregated_text,
            average_confidence=doc_avg_conf,
            total_regions=total_regions_count,
            accuracy=AccuracyMetrics(**accuracy_dict),
            status="success"
        )
