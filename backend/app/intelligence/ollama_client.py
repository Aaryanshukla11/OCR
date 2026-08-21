import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

logger = logging.getLogger("OllamaUnderstandingClient")

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5")
OLLAMA_TIMEOUT_SEC = int(os.getenv("OLLAMA_TIMEOUT", "90"))

class OllamaUnderstandingClient:
    """
    Ollama Client for Qwen General/Instruct LLM Document Understanding.
    Configurable model selection, strict JSON response format, and 60-120s timeout.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model_name: str = DEFAULT_OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT_SEC
    ):
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self._auto_select_model()

    def _auto_select_model(self):
        """Auto-detects available local Ollama models if specified model is not available."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", [])]
                
                # Filter out embedding models
                generative_models = [m for m in models if "embed" not in m.lower()]

                if self.model_name in models or f"{self.model_name}:latest" in models:
                    logger.info(f"Ollama using configured model: '{self.model_name}'")
                    return

                # Check if any qwen instruct model is available
                qwen_models = [m for m in generative_models if "qwen" in m.lower()]
                if qwen_models:
                    self.model_name = qwen_models[0]
                    logger.info(f"Ollama auto-selected Qwen model: '{self.model_name}'")
                elif generative_models:
                    self.model_name = generative_models[0]
                    logger.info(f"Ollama auto-selected generative model: '{self.model_name}'")
                else:
                    logger.warning(f"No generative models found on Ollama at {self.base_url}")
        except Exception as e:
            logger.warning(f"Could not connect to Ollama at {self.base_url}: {e}")

    def analyze_document_text(self, aggregated_text: str, region_snippets: List[str]) -> Optional[Dict[str, Any]]:
        """
        Prompts Qwen LLM via Ollama to perform semantic understanding & structured extraction.
        Returns strict JSON dictionary or None if Ollama is unreachable.
        """
        system_prompt = (
            "You are an expert Document Intelligence AI. Your task is to analyze raw OCR text "
            "and extract structured document information.\n\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Determine the document_type: invoice | receipt | flight_ticket | hotel_invoice | bank_statement | medical_report | contract | form | certificate | unknown\n"
            "2. Extract ALL key-value entities found in the document into an 'entities' list.\n"
            "3. For each entity, specify:\n"
            "   - 'key': snake_case key name (e.g. invoice_number, gstin, total_amount, date, merchant_name, passenger_name, pnr_number)\n"
            "   - 'label': Human readable label (e.g. 'Invoice Number', 'GSTIN', 'Total Amount')\n"
            "   - 'raw_value': Exact text substring as written in the OCR text\n"
            "   - 'value_type': string | date | currency | number\n"
            "4. Return strict JSON matching this exact structure:\n"
            "{\n"
            "  \"document_type\": \"...\",\n"
            "  \"confidence_score\": 0.95,\n"
            "  \"entities\": [\n"
            "    {\"key\": \"invoice_number\", \"label\": \"Invoice Number\", \"raw_value\": \"INV-1024\", \"value_type\": \"string\"}\n"
            "  ]\n"
            "}\n"
            "Respond ONLY with valid JSON."
        )

        user_content = (
            f"DOCUMENT OCR TEXT:\n{aggregated_text[:3000]}\n\n"
            f"OCR REGION SNIPPETS:\n" + "\n".join(region_snippets[:40])
        )

        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\nUSER INPUT:\n{user_content}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_predict": 1024
            }
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=req_data,
                headers={"Content-Type": "application/json"}
            )

            logger.info(f"Sending OCR payload to Qwen LLM via Ollama (model: '{self.model_name}', timeout: {self.timeout}s)...")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                raw_response = resp_data.get("response", "")
                
                # Parse JSON
                parsed_json = json.loads(raw_response)
                logger.info(f"Qwen LLM extraction succeeded. Inferred document_type: '{parsed_json.get('document_type')}'")
                return parsed_json
        except urllib.error.URLError as url_err:
            logger.warning(f"Ollama API connection failed at {self.base_url}: {url_err}")
            return None
        except TimeoutError:
            logger.warning(f"Ollama API request timed out after {self.timeout} seconds")
            return None
        except Exception as err:
            logger.warning(f"Failed to process Ollama response: {err}")
            return None
