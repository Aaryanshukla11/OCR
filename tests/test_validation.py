import pytest
import numpy as np
from app.core.config import ValidationConfig
from app.validation.validator import InputValidator, ValidationError

def test_validate_file_metadata_valid():
    config = ValidationConfig(max_file_size_mb=25, allowed_extensions=[".png", ".jpg", ".pdf"])
    validator = InputValidator(config)
    
    # Should not raise exception
    validator.validate_file_metadata("sample.png", 1024 * 1024)

def test_validate_file_metadata_invalid_extension():
    config = ValidationConfig(max_file_size_mb=25, allowed_extensions=[".png", ".jpg", ".pdf"])
    validator = InputValidator(config)
    
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_file_metadata("exe_file.exe", 500)
    assert "Invalid file extension" in str(excinfo.value)

def test_validate_file_metadata_oversized():
    config = ValidationConfig(max_file_size_mb=5, allowed_extensions=[".png"])
    validator = InputValidator(config)
    
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_file_metadata("big.png", 10 * 1024 * 1024)
    assert "exceeds maximum allowed limit" in str(excinfo.value)

def test_validate_image_array():
    config = ValidationConfig()
    validator = InputValidator(config)
    
    # Valid RGB array
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    validator.validate_image_array(img)
    
    # Invalid grayscale array
    with pytest.raises(ValidationError):
        validator.validate_image_array(np.zeros((100, 100), dtype=np.uint8))
