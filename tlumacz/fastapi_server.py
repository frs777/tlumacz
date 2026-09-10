"""Serwer FastAPI + Transformers dla TranslateGemma.

Ten moduł implementuje serwer HTTP z OpenAI-compatible API który obsługuje
specjalny format TranslateGemma z kodami języków (source_lang_code, target_lang_code).

Wymaga zainstalowanych zależności:
    pip install fastapi uvicorn transformers torch accelerate
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class FastAPIServerConfig:
    """Konfiguracja serwera FastAPI + Transformers."""

    model_path: str = "google/translategemma-4b-it"
    host: str = "127.0.0.1"
    port: int = 8001
    device: str = "auto"  # "auto", "cpu", "cuda"
    dtype: str = "float16"  # "float16", "bfloat16", "float32"


class ContentItem(BaseModel):
    """Element zawartości wiadomości (tekst lub obraz)."""

    type: str  # "text" lub "image"
    source_lang_code: Optional[str] = None
    target_lang_code: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None


class Message(BaseModel):
    """Wiadomość w formacie OpenAI."""

    role: str  # "user" lub "assistant"
    content: str | list[ContentItem]


class ChatCompletionRequest(BaseModel):
    """Żądanie chat completions w formacie OpenAI."""

    model: str
    messages: list[Message]
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 200
    stream: Optional[bool] = False


class ChatCompletionChoice(BaseModel):
    """Wybór w odpowiedzi chat completions."""

    index: int
    message: Message
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    """Odpowiedź chat completions w formacie OpenAI."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]


class TranslateGemmaServer:
    """Serwer TranslateGemma z FastAPI + Transformers.
    
    Ten serwer ładuje model TranslateGemma i udostępnia go przez
    OpenAI-compatible API. Obsługuje specjalny format z kodami języków
    (source_lang_code, target_lang_code) który daje drastyczny wzrost
    jakości tłumaczenia.
    """

    def __init__(self, config: FastAPIServerConfig) -> None:
        self.config = config
        self.app = FastAPI(title="TranslateGemma Server")
        self.processor = None
        self.model = None
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self._setup_routes()
        self._setup_cors()

    def _setup_cors(self) -> None:
        """Konfiguracja CORS dla dostępu z przeglądarki."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Konfiguracja tras FastAPI."""
        
        @self.app.get("/health")
        async def health():
            """Endpoint health check."""
            if self.model is None:
                raise HTTPException(status_code=503, detail="Model not loaded")
            return {"status": "ok", "model": self.config.model_path}

        @self.app.get("/v1/models")
        async def list_models():
            """Lista dostępnych modeli (OpenAI-compatible)."""
            return {
                "object": "list",
                "data": [
                    {
                        "id": self.config.model_path,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "local",
                    }
                ],
            }

        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: ChatCompletionRequest):
            """Endpoint chat completions (OpenAI-compatible).
            
            Obsługuje specjalny format TranslateGemma z kodami języków:
            {
                "role": "user",
                "content": [{
                    "type": "text",
                    "source_lang_code": "en",
                    "target_lang_code": "pl",
                    "text": "Hello world"
                }]
            }
            """
            if self.model is None:
                raise HTTPException(status_code=503, detail="Model not loaded")

            try:
                # Konwertuj wiadomości na format Transformers
                messages = []
                for msg in request.messages:
                    if isinstance(msg.content, str):
                        # Standardowy format tekstowy
                        messages.append({
                            "role": msg.role,
                            "content": [{"type": "text", "text": msg.content}]
                        })
                    else:
                        # Specjalny format z kodami języków
                        content_list = []
                        for item in msg.content:
                            # item może być dict lub ContentItem — normalizuj
                            if isinstance(item, dict):
                                item_type = item.get("type", "text")
                                item_text = item.get("text", "")
                                item_source = item.get("source_lang_code")
                                item_target = item.get("target_lang_code")
                                item_url = item.get("url") or item.get("image")
                            else:
                                item_type = item.type
                                item_text = item.text or ""
                                item_source = item.source_lang_code
                                item_target = item.target_lang_code
                                item_url = item.url or item.image
                            
                            content_item = {"type": item_type}
                            if item_type == "text":
                                content_item["text"] = item_text
                                if item_source:
                                    content_item["source_lang_code"] = item_source
                                if item_target:
                                    content_item["target_lang_code"] = item_target
                            elif item_type == "image":
                                content_item["url"] = item_url
                            content_list.append(content_item)
                        messages.append({
                            "role": msg.role,
                            "content": content_list
                        })

                # Generuj tłumaczenie
                result = self._generate(messages, request.max_tokens, request.temperature)

                return ChatCompletionResponse(
                    id=f"chatcmpl-{int(time.time())}",
                    created=int(time.time()),
                    model=request.model,
                    choices=[
                        ChatCompletionChoice(
                            index=0,
                            message=Message(role="assistant", content=result),
                            finish_reason="stop",
                        )
                    ],
                )
            except Exception as e:
                logger.error(f"Error in chat completions: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _generate(self, messages: list[dict], max_tokens: int, temperature: float) -> str:
        """Generuj tłumaczenie używając modelu TranslateGemma.

        Args:
            messages: Wiadomości w formacie Transformers
            max_tokens: Maksymalna liczba tokenów
            temperature: Temperatura generowania

        Returns:
            Wygenerowany tekst
        """
        import torch

        # Obsługa "auto" jako source_lang_code — zamień na konkretny kod języka
        # TranslateGemma nie obsługuje "auto", wymaga kodów ISO 639-1
        for msg in messages:
            if isinstance(msg.get("content"), list):
                for item in msg["content"]:
                    if isinstance(item, dict) and item.get("source_lang_code") == "auto":
                        # Proste wykrywanie języka — jeśli zawiera polskie znaki, assume "pl"
                        text = item.get("text", "")
                        if any(c in text for c in "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"):
                            item["source_lang_code"] = "pl"
                        else:
                            item["source_lang_code"] = "en"  # Domyślnie angielski

        # Przygotuj input
        inputs = self.processor.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt",
        )
        # Przenieś tensory na urządzenie (dict nie ma metody .to())
        inputs = {k: v.to(self.model.device) if hasattr(v, 'to') else v for k, v in inputs.items()}

        input_len = len(inputs["input_ids"][0])

        # Generuj
        with torch.inference_mode():
            generation = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=temperature if temperature > 0 else 1.0,
            )

        # Dekoduj tylko wygenerowaną część
        generation = generation[0][input_len:]
        decoded = self.processor.decode(generation, skip_special_tokens=True)

        return decoded

    def _get_dtype(self):
        """Pobierz typ danych torch na podstawie konfiguracji.
        
        Na CPU wymuszamy float32 — float16 na CPU powoduje problemy numeryczne (inf/nan).
        Na GPU używamy konfiguracji użytkownika (float16/bfloat16).
        """
        import torch

        # Sprawdź rzeczywiste urządzenie (po konwersji "auto")
        use_cpu = (self.config.device == "cpu") or \
                  (self.config.device == "auto" and not torch.cuda.is_available())
        
        # Na CPU zawsze używaj float32 — float16 jest niestabilne
        if use_cpu:
            return torch.float32
        
        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        return dtype_map.get(self.config.dtype, torch.float16)

    def load_model(self) -> None:
        """Załaduj model TranslateGemma.

        Ta metoda ładuje model i processor z Transformers.
        Obsługuje modele GPTQ (skwantyzowane 4-bit).
        Może zająć dużo czasu i pamięci.
        """
        from transformers import AutoProcessor, AutoModelForImageTextToText

        logger.info(f"Loading model from {self.config.model_path}")

        # Ustaw HF_TOKEN ze zmiennej środowiskowej (jeśli dostępne)
        hf_token = os.environ.get("HF_TOKEN")
        if hf_token:
            logger.info("Using HF_TOKEN from environment")
        else:
            logger.warning("HF_TOKEN not set - gated models will fail to load")

        self.processor = AutoProcessor.from_pretrained(
            self.config.model_path,
            token=hf_token,
        )
        
        device_map = self.config.device
        if device_map == "auto":
            # Sprawdź czy CUDA jest dostępne
            import torch
            if torch.cuda.is_available():
                device_map = "auto"  # Użyj GPU jeśli dostępne
            else:
                device_map = "cpu"  # W przeciwnym razie CPU
        
        # Sprawdź czy to model GPTQ
        model_kwargs = {}
        if "gptq" in self.config.model_path.lower() or "GPTQ" in self.config.model_path:
            logger.info("Detected GPTQ model, using bitsandbytes for quantization")
            # GPTQ models are already quantized, just load them
            model_kwargs["torch_dtype"] = self._get_dtype()
        else:
            model_kwargs["torch_dtype"] = self._get_dtype()
        
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.config.model_path,
            device_map=device_map,
            token=hf_token,
            **model_kwargs,
        )
        
        logger.info(f"Model loaded successfully on {self.model.device}")

    def start(self) -> None:
        """Uruchom serwer w osobnym wątku.

        Model jest ładowany synchronicznie — ta metoda jest wywoływana
        z QThread (FastAPIStartWorker w BackendManager), więc nie blokuje GUI.
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Server already running")
            return

        # Załaduj model synchronicznie (wywoływane z QThread, nie blokuje GUI)
        if self.model is None:
            logger.info("Loading model...")
            self.load_model()
            logger.info("Model loaded successfully")

        # Uruchom serwer
        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level="info",
            access_log=False,
        )
        self._server = uvicorn.Server(config)

        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

        logger.info(f"Server started on http://{self.config.host}:{self.config.port}")

    def stop(self) -> None:
        """Zatrzymaj serwer."""
        if self._server is not None:
            self._server.should_exit = True
            if self._thread is not None:
                self._thread.join(timeout=5)
            self._server = None
            self._thread = None
            logger.info("Server stopped")

    def is_running(self) -> bool:
        """Sprawdź czy serwer działa."""
        return self._thread is not None and self._thread.is_alive()


def create_server(config: Optional[FastAPIServerConfig] = None) -> TranslateGemmaServer:
    """Utwórz serwer TranslateGemma.
    
    Args:
        config: Konfiguracja serwera (opcjonalna)
        
    Returns:
        Instancja TranslateGemmaServer
    """
    if config is None:
        config = FastAPIServerConfig()
    return TranslateGemmaServer(config)


if __name__ == "__main__":
    # Uruchom serwer z linii poleceń
    import sys
    
    model_path = sys.argv[1] if len(sys.argv) > 1 else "google/translategemma-4b-it"
    host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8001
    
    config = FastAPIServerConfig(
        model_path=model_path,
        host=host,
        port=port,
    )
    
    server = create_server(config)
    server.start()
    
    logger.info(f"Server running on http://{host}:{port}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
