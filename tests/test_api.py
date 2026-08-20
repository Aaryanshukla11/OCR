from fastapi.testclient import TestClient
from app.main import app
from tests.test_pipeline import create_synthetic_test_image

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "engine" in data
    assert data["provider"] == "PaddleOCR"

def test_api_ocr_endpoint():
    img_bytes = create_synthetic_test_image()
    files = {"file": ("test_synthetic.png", img_bytes, "image/png")}
    data = {"ground_truth": "OCR ENGINE TEST"}
    
    response = client.post("/api/ocr", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["filename"] == "test_synthetic.png"
    assert "processing_time" in res_data
    assert "average_confidence" in res_data
