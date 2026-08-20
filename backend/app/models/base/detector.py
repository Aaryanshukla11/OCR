from abc import ABC, abstractmethod
from typing import List
import numpy as np

class BaseDetector(ABC):
    """
    Abstract Interface for Text Detection Models.
    Future models (e.g. DBNet, CRAFT, custom detectors) must implement this interface.
    """
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[List[List[float]]]:
        """
        Detects text bounding boxes in an image.
        Returns a list of polygons: [[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ...]
        """
        pass
