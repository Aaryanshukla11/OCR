import os
from typing import List, Tuple
import numpy as np
from app.core.config import ValidationConfig

class ValidationError(Exception):
    pass

class InputValidator:
    """
    Lightweight validation layer for input files, image dimensions,
    and output region sanity bounds.
    """
    def __init__(self, config: ValidationConfig):
        self.config = config

    def validate_file_metadata(self, filename: str, file_size_bytes: int):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.config.allowed_extensions:
            raise ValidationError(
                f"Invalid file extension '{ext}'. Allowed extensions: {self.config.allowed_extensions}"
            )
            
        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        if file_size_bytes > max_bytes:
            raise ValidationError(
                f"File size {file_size_bytes} bytes exceeds maximum allowed limit of {self.config.max_file_size_mb} MB"
            )

    def validate_image_array(self, image: np.ndarray):
        if not isinstance(image, np.ndarray):
            raise ValidationError("Invalid input image: expected NumPy ndarray")
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValidationError(f"Invalid image dimensions: expected (H, W, 3) RGB array, got shape {image.shape}")
        if image.shape[0] < 10 or image.shape[1] < 10:
            raise ValidationError(f"Image dimensions {image.shape[:2]} are too small for OCR processing (minimum 10x10)")

    def sanitize_regions(self, regions: List[dict], img_width: int, img_height: int) -> List[dict]:
        sanitized = []
        for r in regions:
            bbox = r.get("bbox", [0.0, 0.0, 0.0, 0.0])
            # Clamp bbox values to image boundaries
            xmin = max(0.0, min(float(bbox[0]), float(img_width)))
            ymin = max(0.0, min(float(bbox[1]), float(img_height)))
            xmax = max(xmin, min(float(bbox[2]), float(img_width)))
            ymax = max(ymin, min(float(bbox[3]), float(img_height)))
            
            conf = max(0.0, min(float(r.get("confidence", 0.0)), 1.0))
            
            sanitized.append({
                "id": r.get("id", 1),
                "text": str(r.get("text", "")),
                "polygon": r.get("polygon", []),
                "bbox": [xmin, ymin, xmax, ymax],
                "confidence": round(conf, 4)
            })
        return sanitized
