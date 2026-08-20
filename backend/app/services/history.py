import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "history.json")

def _ensure_history_file():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def get_history() -> List[Dict[str, Any]]:
    _ensure_history_file()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def add_history_entry(filename: str, processing_time: float, total_regions: int, 
                       average_confidence: float, device: str, status: str, 
                       file_type: str, pages_count: int) -> Dict[str, Any]:
    history = get_history()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "filename": filename,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processing_time": round(processing_time, 2),
        "total_regions": total_regions,
        "average_confidence": round(average_confidence * 100, 1) if average_confidence <= 1.0 else round(average_confidence, 1),
        "device": device,
        "status": status,
        "file_type": file_type,
        "pages_count": pages_count
    }
    # Prepend to keep newest first
    history.insert(0, entry)
    # Keep up to 100 items
    history = history[:100]
    
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
        
    return entry

def clear_history():
    _ensure_history_file()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
