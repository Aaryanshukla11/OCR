import os
import yaml
from dataclasses import dataclass, field
from typing import List

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "ocr_config.yaml"))

@dataclass
class EngineConfig:
    name: str = "Our OCR Engine"
    version: str = "1.0.0"

@dataclass
class OCRModelConfig:
    provider: str = "paddleocr"
    device: str = "auto"
    lang: str = "en"

@dataclass
class PreprocessingConfig:
    enabled: bool = True
    deskew: bool = False
    denoise: bool = False
    contrast: bool = False
    max_side_len: int = 4000

@dataclass
class PostprocessingConfig:
    enabled: bool = True
    normalize_whitespace: bool = True
    sort_reading_order: bool = True

@dataclass
class ValidationConfig:
    max_file_size_mb: int = 25
    allowed_extensions: List[str] = field(default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp", ".pdf"])

@dataclass
class AppConfig:
    engine: EngineConfig = field(default_factory=EngineConfig)
    ocr: OCRModelConfig = field(default_factory=OCRModelConfig)
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    postprocessing: PostprocessingConfig = field(default_factory=PostprocessingConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)

def load_config() -> AppConfig:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                
            return AppConfig(
                engine=EngineConfig(**data.get("engine", {})),
                ocr=OCRModelConfig(**data.get("ocr", {})),
                preprocessing=PreprocessingConfig(**data.get("preprocessing", {})),
                postprocessing=PostprocessingConfig(**data.get("postprocessing", {})),
                validation=ValidationConfig(**data.get("validation", {}))
            )
        except Exception as e:
            print(f"Warning: Failed to parse {CONFIG_PATH}, using default config: {e}")
            return AppConfig()
    return AppConfig()
