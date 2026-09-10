"""Testy modułu fastapi_server.py — serwer TranslateGemma z FastAPI.

Te testy weryfikują:
- Inicjalizację serwera i konfigurację
- Specjalny format TranslateGemma (source_lang_code, target_lang_code)
- Endpointy FastAPI (/health, /v1/models, /v1/chat/completions)
- Konwersję wiadomości na format Transformers
- Obsługę dtype (float16, bfloat16, float32)

Uwaga: testy NIE wymagają prawdziwego modelu ani GPU.
Wszystkie ciężkie zależności (torch, transformers) są mockowane.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import time


# ============================================================================
# Testy konfiguracji
# ============================================================================

class TestFastAPIServerConfig:
    """Testy klasy FastAPIServerConfig."""

    def test_default_config(self):
        """Domyślna konfiguracja powinna mieć rozsądne wartości."""
        from tlumacz.fastapi_server import FastAPIServerConfig

        config = FastAPIServerConfig()
        assert config.model_path == "google/translategemma-4b-it"
        assert config.host == "127.0.0.1"
        assert config.port == 8001
        assert config.device == "auto"
        assert config.dtype == "float16"

    def test_custom_config(self):
        """Można utworzyć konfigurację z niestandardowymi wartościami."""
        from tlumacz.fastapi_server import FastAPIServerConfig

        config = FastAPIServerConfig(
            model_path="/path/to/model",
            host="0.0.0.0",
            port=9000,
            device="cpu",
            dtype="float32",
        )
        assert config.model_path == "/path/to/model"
        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.device == "cpu"
        assert config.dtype == "float32"


# ============================================================================
# Testy modeli Pydantic (request/response)
# ============================================================================

class TestPydanticModels:
    """Testy modeli Pydantic dla request/response."""

    def test_content_item_text(self):
        """ContentItem dla tekstu z kodami języków."""
        from tlumacz.fastapi_server import ContentItem

        item = ContentItem(
            type="text",
            source_lang_code="en",
            target_lang_code="pl",
            text="Hello world",
        )
        assert item.type == "text"
        assert item.source_lang_code == "en"
        assert item.target_lang_code == "pl"
        assert item.text == "Hello world"

    def test_content_item_image(self):
        """ContentItem dla obrazu."""
        from tlumacz.fastapi_server import ContentItem

        item = ContentItem(
            type="image",
            url="https://example.com/image.jpg",
        )
        assert item.type == "image"
        assert item.url == "https://example.com/image.jpg"

    def test_message_string_content(self):
        """Message z content jako string."""
        from tlumacz.fastapi_server import Message

        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_list_content(self):
        """Message z content jako lista ContentItem."""
        from tlumacz.fastapi_server import Message, ContentItem

        msg = Message(
            role="user",
            content=[
                ContentItem(
                    type="text",
                    source_lang_code="en",
                    target_lang_code="pl",
                    text="Hello",
                )
            ],
        )
        assert msg.role == "user"
        assert isinstance(msg.content, list)
        assert len(msg.content) == 1
        assert msg.content[0].source_lang_code == "en"

    def test_chat_completion_request(self):
        """ChatCompletionRequest z pełnymi danymi."""
        from tlumacz.fastapi_server import ChatCompletionRequest, Message

        request = ChatCompletionRequest(
            model="test-model",
            messages=[Message(role="user", content="Hello")],
            temperature=0.5,
            max_tokens=100,
        )
        assert request.model == "test-model"
        assert len(request.messages) == 1
        assert request.temperature == 0.5
        assert request.max_tokens == 100

    def test_chat_completion_response(self):
        """ChatCompletionResponse z pełnymi danymi."""
        from tlumacz.fastapi_server import (
            ChatCompletionResponse,
            ChatCompletionChoice,
            Message,
        )

        response = ChatCompletionResponse(
            id="chatcmpl-123",
            created=1234567890,
            model="test-model",
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=Message(role="assistant", content="Witaj"),
                    finish_reason="stop",
                )
            ],
        )
        assert response.id == "chatcmpl-123"
        assert response.object == "chat.completion"
        assert len(response.choices) == 1
        assert response.choices[0].message.content == "Witaj"


# ============================================================================
# Testy TranslateGemmaServer
# ============================================================================

class TestTranslateGemmaServer:
    """Testy klasy TranslateGemmaServer."""

    def test_server_init(self):
        """Serwer powinien się tworzyć bez błędów."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)

        assert server.config == config
        assert server.app is not None
        assert server.processor is None  # nie załadowany
        assert server.model is None  # nie załadowany
        assert server._server is None  # nie uruchomiony
        assert server._thread is None

    def test_server_not_running_initially(self):
        """Serwer nie powinien działać po utworzeniu."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)

        assert not server.is_running()

    def test_server_has_fastapi_app(self):
        """Serwer powinien mieć instancję FastAPI."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)

        assert server.app is not None
        assert server.app.title == "TranslateGemma Server"

    def test_get_dtype_float16(self):
        """_get_dtype powinno zwracać torch.float16 dla dtype='float16'."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig

        config = FastAPIServerConfig(dtype="float16")
        server = TranslateGemmaServer(config)

        # Mock torch
        mock_torch = MagicMock()
        mock_torch.float16 = "float16"
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.float32 = "float32"

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = server._get_dtype()
            assert result == "float16"

    def test_get_dtype_float32(self):
        """_get_dtype powinno zwracać torch.float32 dla dtype='float32'."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig

        config = FastAPIServerConfig(dtype="float32")
        server = TranslateGemmaServer(config)

        mock_torch = MagicMock()
        mock_torch.float16 = "float16"
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.float32 = "float32"

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = server._get_dtype()
            assert result == "float32"

    def test_get_dtype_bfloat16(self):
        """_get_dtype powinno zwracać torch.bfloat16 dla dtype='bfloat16'."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig

        config = FastAPIServerConfig(dtype="bfloat16")
        server = TranslateGemmaServer(config)

        mock_torch = MagicMock()
        mock_torch.float16 = "float16"
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.float32 = "float32"

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = server._get_dtype()
            assert result == "bfloat16"

    def test_get_dtype_unknown_falls_back_to_float16(self):
        """_get_dtype powinno fallbackować do float16 dla nieznanego dtype."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig

        config = FastAPIServerConfig(dtype="unknown")
        server = TranslateGemmaServer(config)

        mock_torch = MagicMock()
        mock_torch.float16 = "float16"
        mock_torch.bfloat16 = "bfloat16"
        mock_torch.float32 = "float32"

        with patch.dict("sys.modules", {"torch": mock_torch}):
            result = server._get_dtype()
            assert result == "float16"


# ============================================================================
# Testy specjalnego formatu TranslateGemma
# ============================================================================

class TestTranslateGemmaFormat:
    """Testy specjalnego formatu TranslateGemma z kodami języków."""

    def test_special_format_structure(self):
        """Specjalny format powinien mieć source_lang_code i target_lang_code."""
        from tlumacz.fastapi_server import ContentItem

        item = ContentItem(
            type="text",
            source_lang_code="en",
            target_lang_code="pl",
            text="Hello world",
        )

        # Sprawdź że wszystkie pola są ustawione
        assert item.type == "text"
        assert item.source_lang_code == "en"
        assert item.target_lang_code == "pl"
        assert item.text == "Hello world"

    def test_auto_source_lang(self):
        """source_lang_code może być 'auto' dla auto-detekcji."""
        from tlumacz.fastapi_server import ContentItem

        item = ContentItem(
            type="text",
            source_lang_code="auto",
            target_lang_code="pl",
            text="Hello world",
        )
        assert item.source_lang_code == "auto"

    def test_optional_lang_codes(self):
        """Kody języków są opcjonalne."""
        from tlumacz.fastapi_server import ContentItem

        item = ContentItem(type="text", text="Hello")
        assert item.source_lang_code is None
        assert item.target_lang_code is None


# ============================================================================
# Testy factory function
# ============================================================================

class TestCreateServer:
    """Testy funkcji create_server()."""

    def test_create_server_default(self):
        """create_server() bez argumentów powinna użyć domyślnej konfiguracji."""
        from tlumacz.fastapi_server import create_server

        server = create_server()
        assert server is not None
        assert server.config.model_path == "google/translategemma-4b-it"

    def test_create_server_custom_config(self):
        """create_server() z konfiguracją powinna użyć niestandardowych wartości."""
        from tlumacz.fastapi_server import create_server, FastAPIServerConfig

        config = FastAPIServerConfig(
            model_path="/custom/model",
            port=9999,
        )
        server = create_server(config)
        assert server.config.model_path == "/custom/model"
        assert server.config.port == 9999


# ============================================================================
# Testy endpointów FastAPI (z mockowanym modelem)
# ============================================================================

class TestFastAPIEndpoints:
    """Testy endpointów FastAPI z mockowanym modelem."""

    def test_health_endpoint_model_not_loaded(self):
        """Endpoint /health powinien zwrócić 503 gdy model nie jest załadowany."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig
        from fastapi.testclient import TestClient

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)
        # model = None (nie załadowany)

        client = TestClient(server.app)
        response = client.get("/health")

        assert response.status_code == 503
        assert "Model not loaded" in response.json()["detail"]

    def test_health_endpoint_model_loaded(self):
        """Endpoint /health powinien zwrócić 200 gdy model jest załadowany."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig
        from fastapi.testclient import TestClient

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)
        server.model = MagicMock()  # mock załadowanego modelu

        client = TestClient(server.app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["model"] == config.model_path

    def test_list_models_endpoint(self):
        """Endpoint /v1/models powinien zwrócić listę modeli."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig
        from fastapi.testclient import TestClient

        config = FastAPIServerConfig(model_path="test-model")
        server = TranslateGemmaServer(config)

        client = TestClient(server.app)
        response = client.get("/v1/models")

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "test-model"

    def test_chat_completions_model_not_loaded(self):
        """Endpoint /v1/chat/completions powinien zwrócić 503 gdy model nie jest załadowany."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig
        from fastapi.testclient import TestClient

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)

        client = TestClient(server.app)
        response = client.post("/v1/chat/completions", json={
            "model": "test",
            "messages": [{"role": "user", "content": "Hello"}],
        })

        assert response.status_code == 503

    def test_chat_completions_standard_format(self):
        """Endpoint /v1/chat/completions z standardowym formatem tekstowym."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig
        from fastapi.testclient import TestClient

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)
        server.model = MagicMock()
        server.processor = MagicMock()

        # Mock _generate
        server._generate = MagicMock(return_value="Witaj świecie")

        client = TestClient(server.app)
        response = client.post("/v1/chat/completions", json={
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello world"}],
            "temperature": 0.1,
            "max_tokens": 100,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["content"] == "Witaj świecie"

    def test_chat_completions_translategemma_format(self):
        """Endpoint /v1/chat/completions ze specjalnym formatem TranslateGemma."""
        from tlumacz.fastapi_server import TranslateGemmaServer, FastAPIServerConfig
        from fastapi.testclient import TestClient

        config = FastAPIServerConfig()
        server = TranslateGemmaServer(config)
        server.model = MagicMock()
        server.processor = MagicMock()

        # Mock _generate
        server._generate = MagicMock(return_value="Witaj świecie")

        client = TestClient(server.app)
        response = client.post("/v1/chat/completions", json={
            "model": "test-model",
            "messages": [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "source_lang_code": "en",
                    "target_lang_code": "pl",
                    "text": "Hello world",
                }]
            }],
            "temperature": 0.1,
            "max_tokens": 100,
        })

        assert response.status_code == 200
        data = response.json()
        assert data["choices"][0]["message"]["content"] == "Witaj świecie"

        # Sprawdź że _generate został wywołany z poprawnym formatem
        call_args = server._generate.call_args
        messages = call_args[0][0]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        content = messages[0]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "text"
        assert content[0]["source_lang_code"] == "en"
        assert content[0]["target_lang_code"] == "pl"
        assert content[0]["text"] == "Hello world"
