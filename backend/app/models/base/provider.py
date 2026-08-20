from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np

class BaseOCRProvider(ABC):
    """
    Abstract Interface for End-to-End OCR Model Providers.
    Encapsulates model initialization, device placement, and inference execution.
    """
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def device(self) -> str:
        pass

    @abstractmethod
    def process_image(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Executes OCR on a single normalized image.
        Returns a standardized list of raw region dicts:
        [
            {
                "id": 1,
                "text": "Extracted Text",
                "confidence": 0.98,
                "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
                "bbox": [xmin, ymin, xmax, ymax]
            }, ...
        ]
        """
        pass
