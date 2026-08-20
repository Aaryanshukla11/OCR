from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

class BaseRecognizer(ABC):
    """
    Abstract Interface for Text Recognition Models.
    Future models (e.g. TrOCR, CRNN, SVTR, custom handwriting models) must implement this interface.
    """
    @abstractmethod
    def recognize(self, image: np.ndarray, boxes: List[List[List[float]]]) -> List[Tuple[str, float]]:
        """
        Recognizes text from image regions specified by boxes.
        Returns a list of tuples: [("text", confidence_score), ...]
        """
        pass
