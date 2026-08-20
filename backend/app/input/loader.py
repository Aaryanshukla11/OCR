import io
from typing import Tuple
import numpy as np
from PIL import Image

class ImageLoader:
    """
    Input layer image loader for PNG, JPG, JPEG, WEBP files.
    Converts raw bytes or file paths to normalized RGB NumPy arrays.
    """
    @staticmethod
    def load_from_bytes(file_bytes: bytes) -> Tuple[np.ndarray, int, int]:
        image = Image.open(io.BytesIO(file_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        width, height = image.size
        return np.array(image), width, height

    @staticmethod
    def load_from_path(file_path: str) -> Tuple[np.ndarray, int, int]:
        image = Image.open(file_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        width, height = image.size
        return np.array(image), width, height
