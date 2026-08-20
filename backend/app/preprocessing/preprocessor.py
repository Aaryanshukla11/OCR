import cv2
import numpy as np
from app.core.config import PreprocessingConfig

class Preprocessor:
    """
    Configurable preprocessing pipeline.
    By default prioritizes preserving the original input image.
    """
    def __init__(self, config: PreprocessingConfig):
        self.config = config

    def process(self, image: np.ndarray) -> np.ndarray:
        if not self.config.enabled:
            return image

        processed = image.copy()
        
        # Optional Max Side Length Resize
        h, w = processed.shape[:2]
        max_len = self.config.max_side_len
        if max(h, w) > max_len:
            scale = max_len / float(max(h, w))
            new_w, new_h = int(w * scale), int(h * scale)
            processed = cv2.resize(processed, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Optional Contrast Enhancement
        if self.config.contrast:
            lab = cv2.cvtColor(processed, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            processed = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2RGB)

        # Optional Denoising
        if self.config.denoise:
            processed = cv2.fastNlMeansDenoisingColored(processed, None, 5, 5, 7, 21)

        return processed
