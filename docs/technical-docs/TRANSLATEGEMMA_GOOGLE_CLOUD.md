# TranslateGemma — Dokumentacja z Google Cloud Console

**Źródło:** https://console.cloud.google.com/agent-platform/publishers/google/model-garden/translategemma  
**Data zrzutu:** 2026-09-06

---

## 📋 Opis

**TranslateGemma** to rodzina lekkich, najnowocześniejszych otwartych modeli tłumaczeniowych firmy Google, oparta na rodzinie modeli Gemma 3.

Modele TranslateGemma zostały zaprojektowane do obsługi zadań tłumaczeniowych w **55 językach**. Ich stosunkowo niewielkie rozmiary umożliwiają wdrażanie ich w środowiskach o ograniczonych zasobach, takich jak laptopy, komputery stacjonarne czy własna infrastruktura chmurowa.

---

## 🎯 Przypadki użycia

**Tłumaczenie:**
- Przyjmuje tekst lub obrazy jako dane wejściowe
- Generuje tłumaczenie

---

## 💬 Specjalny szablon czatu

TranslateGemma został zaprojektowany do pracy ze **specjalnym szablonem czatu**, który obsługuje:
- Bezpośrednie tłumaczenie wprowadzonego tekstu
- Ekstrakcję tekstu i tłumaczenie z wprowadzonego obrazu

Szablon czatu został zaimplementowany w systemie szablonów czatu **Hugging Face transformers** i jest zgodny z funkcją `apply_chat_template()` udostępnianą przez tokenizator Gemma / procesor Gemma 3.

### Do istotnych różnic w stosunku do innych modeli należą:

1. **TranslateGemma obsługuje tylko role Użytkownika i Asystenta** (brak role="system")

2. **Rola użytkownika jest bardzo specyficzna:**
   - Właściwość `content` musi być podana w postaci listy zawierającej dokładnie jeden wpis
   - Wpis na liście treści musi zawierać:
     - `"type"`: `"text"` lub `"image"`
     - `"source_lang_code"`: kod języka źródłowego (ISO 639-1)
     - `"target_lang_code"`: kod języka docelowego (ISO 639-1)
   - Wpis powinien zawierać jeden z:
     - `"url"`: jeśli typ to "image" (URL do obrazu)
     - `"text"`: jeśli typ to "text" (tekst do tłumaczenia)

3. **Kody języków:**
   - Kod ISO 639-1 Alpha-2 (np. `en`, `pl`, `cs`)
   - Wariant zregionalizowany: ISO 639-1 + ISO 3166-1 (np. `en_US`, `en-GB`, `de-DE`)

4. **Błąd:** Jeśli kod języka nie jest obsługiwany, szablon zgłosi błąd

---

## 🛠️ Wdrażanie przez Vertex AI

### Wdrożenie modelu składa się z 3 kroków:

1. Utworzenie zasobu punktu końcowego
2. Przesłanie modelu
3. Wdrożenie modelu do punktu końcowego

### Przykładowe wdrożenie (Python):

```python
import vertexai
from vertexai import model_garden

PROJECT_ID = ""
REGION = ""

vertexai.init(
    project=PROJECT_ID,
    location=REGION,
)

base_model_name = "translategemma-27b-it"
publisher_model_name = f"publishers/google/models/{base_model_name.lower()}"

model = model_garden.OpenModel(publisher_model_name)
endpoint = model.deploy(accept_eula=True)
```

### Przykładowe żądanie Pythona (standardowa predykcja):

```python
instances = [
    {
        "@requestFormat": "chatCompletions",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "W najgorszym przypadku i k prasknutí čočky.",
                        "source_lang_code": "cs",
                        "target_lang_code": "en"
                    }
                ]
            }
        ],
        "max_tokens": 100
    }
]

response = endpoint.predict(instances=instances)
print(response.predictions["choices"][0]["message"]["content"])
```

### Przykładowe żądanie curl (Chat Completions API):

**Publiczny dedykowany punkt końcowy:**
```bash
curl https://${ENDPOINT_ID}.${DNS_SUFFIX}/v1/projects/${PROJECT_ID}/locations/${REGION}/endpoints/${ENDPOINT_ID}/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -d '{
        "model": "my-model",
        "messages": [
            {
                "role": "user",
                "content": "What is a car?"
            }
        ],
        "max_tokens": 128
    }'
```

**Publiczny wspólny punkt końcowy:**
```bash
curl https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/endpoints/${ENDPOINT_ID}/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -d '{
        "model": "my-model",
        "messages": [
            {
                "role": "user",
                "content": "What is a car?"
            }
        ],
        "max_tokens": 128
    }'
```

### Przykładowe żądanie Pythona (OpenAI-compatible):

```python
use_dedicated_endpoint = True

if use_dedicated_endpoint:
    DEDICATED_ENDPOINT_DNS = endpoint.gca_resource.dedicated_endpoint_dns
    ENDPOINT_RESOURCE_NAME = endpoint.resource_name

# pip install -qU openai requests google-auth
user_message = "How is your day?"
max_tokens = 50
temperature = 1.0
stream = False

import google.auth
import openai

creds, project = google.auth.default()
auth_req = google.auth.transport.requests.Request()
creds.refresh(auth_req)

BASE_URL = f"https://{REGION}-aiplatform.googleapis.com/v1beta1/{ENDPOINT_RESOURCE_NAME}"

try:
    if use_dedicated_endpoint:
        BASE_URL = f"https://{DEDICATED_ENDPOINT_DNS}/v1beta1/{ENDPOINT_RESOURCE_NAME}"
except NameError:
    pass

client = openai.OpenAI(base_url=BASE_URL, api_key=creds.token)

model_response = client.chat.completions.create(
    model="",
    messages=[{"role": "user", "content": user_message}],
    temperature=temperature,
    max_tokens=max_tokens,
    stream=stream,
)
```

---

## 📊 Przykładowa odpowiedź modelu

```json
{
    "predictions": [
        {
            "choices": [
                {
                    "finish_reason": "length",
                    "index": 0,
                    "logprobs": null,
                    "message": {
                        "annotations": null,
                        "audio": null,
                        "content": "Worst case scenario, it could even cause the lens to crack.",
                        "function_call": null,
                        "reasoning": null,
                        "reasoning_content": null,
                        "refusal": null,
                        "role": "assistant",
                        "tool_calls": [],
                        "stop_reason": null,
                        "token_ids": null
                    }
                }
            ]
        }
    ]
}
```

---

## 🎯 Kluczowe wnioski dla projektu Tłumacz

### 1. TranslateGemma przez Vertex AI
- ✅ **Działa** z OpenAI-compatible API
- ✅ **Obsługuje** specjalny format z kodami języków
- ❌ **Wymaga** projektu Google Cloud z billingiem
- ❌ **Koszt** — płatne za użycie

### 2. TranslateGemma lokalnie (Transformers)
- ✅ **Darmowe** — lokalne uruchomienie
- ✅ **Obsługuje** specjalny format z kodami języków
- ⚠️ **Wymaga** 8-54 GB RAM (zależnie od rozmiaru modelu)
- ⚠️ **Wymaga** zatwierdzenia od Google na HuggingFace

### 3. llama.cpp / GGUF
- ❌ **NIE obsługuje** specjalnego formatu z kodami języków
- ❌ Model działa jak zwykły Gemma 3 (niższa jakość)

---

## 🚀 Rekomendacja

**Dla projektu Tłumacz:**

| Opcja | Jakość | Koszt | Trudność | Rekomendacja |
|-------|--------|-------|----------|--------------|
| Vertex AI | ⭐⭐⭐⭐⭐ | 💰 Płatne | Łatwa | Dla produkcji |
| Transformers (lokalnie) | ⭐⭐⭐⭐⭐ | ✅ Darmowe | Średnia | **NAJLEPSZA OPCJA** |
| llama.cpp | ⭐⭐ | ✅ Darmowe | Łatwa | Nie rekomendowane |

**Najlepsza opcja:** Lokalny serwer FastAPI + Transformers z TranslateGemma 4B (float16, ~8GB RAM)

---

**Ostatnia aktualizacja:** 2026-09-06  
**Status:** Kompletna dokumentacja z Google Cloud Console
