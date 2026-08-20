import os
# Set environment flags BEFORE importing paddle or any submodules
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_onednn'] = '0'
os.environ['PADDLE_DISABLE_ONEDNN'] = '1'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.endpoints import router as api_router
from app.core.pipeline import OCRPipeline

app = FastAPI(
    title="Our OCR Engine API",
    description="Modular Document OCR & Evaluation Engine Backend",
    version="1.0.0"
)

# CORS Middleware setup - Allow all network devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route redirect to Interactive API Docs
@app.get("/")
def root_redirect():
    return RedirectResponse(url="/docs")

# Include API router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    print("FastAPI server startup: Eagerly initializing OCR Pipeline Orchestrator...")
    OCRPipeline.get_instance()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
