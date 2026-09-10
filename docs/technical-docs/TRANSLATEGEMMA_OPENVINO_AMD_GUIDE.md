# TranslateGemma z OpenVINO na Linux + AMD (CPU + zintegrowane GPU)

**Data utworzenia:** 2026-09-06  
**Wersja:** 1.0  
**System:** Linux z procesorem AMD (wbudowane GPU Radeon)

---

## Spis treści

1. [OpenVINO vs ONNX Runtime](#1-openvino-vs-onnx-runtime)
2. [Czy OpenVINO działa jak ONNX?](#2-czy-openvino-działa-jak-onnx)
3. [OpenVINO dla AMD — możliwości](#3-openvino-dla-amd--możliwości)
4. [Architektura rozwiązania](#4-architektura-rozwiązania)
5. [Implementacja krok po kroku](#5-implementacja-krok-po-kroku)
6. [Optymalizacja dla zintegrowanego GPU AMD](#6-optymalizacja-dla-zintegrowanego-gpu-amd)
7. [Porównanie wydajności](#7-porównanie-wydajności)
8. [Rozwiązywanie problemów](#8-rozwiązywanie-problemów)
9. [Podsumowanie](#9-podsumowanie)

---

## 1. OpenVINO vs ONNX Runtime

### Kluczowe różnice

| Cecha | ONNX Runtime | OpenVINO |
|-------|--------------|----------|
| **Twórca** | Microsoft | Intel |
| **Format modelu** | ONNX (.onnx) | IR (.xml + .bin) lub ONNX |
| **Główny nacisk** | Cross-platform inference | Optymalizacja Intel/AMD hardware |
| **CPU support** | ✅ Dobry | ✅ **Wyśmienity** (Intel MKL-DNN) |
| **GPU support** | ✅ CUDA, DirectML, ROCm | ⚠️ **Intel iGPU** (AMD eksperymentalne) |
| **NPU support** | ✅ Intel NPU | ✅ **Intel NPU** (najlepszy) |
| **Konwersja modelu** | Nie potrzebna | Wymaga konwersji do IR |
| **Optymalizacje** | Graph optimization | **Quantization, pruning, compression** |
| **Dla AMD CPU** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Dla AMD iGPU** | ⭐⭐ (ROCm) | ⭐ (wymaga testów, często fallback na CPU) |

### Czy OpenVINO działa jak ONNX?

**TAK i NIE:**

✅ **Podobieństwa:**
- Oba służą do inferencji modeli AI
- Oba obsługują modele ONNX (OpenVINO może je zaimportować)
- Oba mają API Python/C++
- Oba optymalizują wydajność

❌ **Różnice:**
- OpenVINO wymaga **konwersji modelu** do formatu IR (.xml + .bin)
- OpenVINO ma **lepsze optymalizacje** dla Intel/AMD hardware
- OpenVINO ma **wbudowane narzędzia** do quantization i compression
- OpenVINO **lepiej wspiera zintegrowane GPU** (iGPU)

### Jak to działa:

```
Model TranslateGemma (ONNX)
    ↓
OpenVINO Model Converter (omz_converter)
    ↓
Model IR (XML + BIN)
    ↓
OpenVINO Runtime
    ├─ CPU (Intel/AMD)
    ├─ GPU (Intel iGPU / AMD iGPU)
    └─ NPU (Intel)
    ↓
Inferencja
```

---

## 2. Czy OpenVINO działa jak ONNX?

### Odpowiedź: OpenVINO może uruchamiać modele ONNX

**Opcja 1: Bezpośrednio z ONNX (wygodne, wolniejsze)**
```python
from openvino.runtime import Core

core = Core()
# OpenVINO automatycznie konwertuje ONNX w runtime
model = core.read_model("model.onnx")
compiled_model = core.compile_model(model, "CPU")
```

**Opcja 2: Konwersja do IR (optymalne, szybsze)**
```bash
# Konwertuj ONNX do IR
ovc --input_model model.onnx --output_dir translated_model/

# Wynik: translated_model.xml + translated_model.bin
```

```python
from openvino.runtime import Core

core = Core()
# Załaduj już skonwertowany model IR
model = core.read_model("translated_model/model.xml")
compiled_model = core.compile_model(model, "GPU")  # lub "CPU"
```

### Rekomendacja dla AMD:

| Scenariusz | Podejście | Uzasadnienie |
|------------|-----------|--------------|
| **Szybki start** | ONNX bezpośrednio | Wygodne, bez konwersji |
| **Maksymalna wydajność** | Konwersja do IR + quantization | Optymalne dla AMD hardware |
| **Zintegrowane GPU AMD** | Konwersja do IR + GPU device | Wykorzystanie iGPU |

---

## 3. OpenVINO dla AMD — możliwości

### 3.1 Wsparcie hardware

| Komponent | Wsparcie OpenVINO | Uwagi |
|-----------|-------------------|-------|
| **AMD CPU (Ryzen)** | ✅ ✅ ✅ Pełne | Optymalizacje MKL-DNN |
| **AMD iGPU (Radeon Vega)** | ✅ ✅ Eksperymentalne | OpenVINO GPU plugin |
| **AMD dGPU (Radeon RX)** | ✅ ✅ Eksperymentalne | OpenVINO GPU plugin |
| **Intel CPU** | ✅ ✅ ✅ Najlepsze | Natywne optymalizacje |
| **Intel iGPU** | ✅ ✅ ✅ Najlepsze | Natywne wsparcie |

### 3.2 Execution devices dla AMD

```python
from openvino.runtime import Core

core = Core()

# Sprawdź dostępne urządzenia
available_devices = core.available_devices
print("Dostępne urządzenia:", available_devices)
# Output: ['CPU', 'GPU.0'] (jeśli masz iGPU)

# Opcja 1: CPU (najstabilniejsze)
compiled_model = core.compile_model(model, "CPU")

# Opcja 2: GPU (zintegrowane AMD Radeon)
compiled_model = core.compile_model(model, "GPU")

# Opcja 3: AUTO (automatyczny wybór)
compiled_model = core.compile_model(model, "AUTO")

# Opcja 4: MULTI (wszystkie dostępne)
compiled_model = core.compile_model(model, "MULTI:CPU,GPU")
```

### 3.3 Optymalizacje dla AMD

**OpenVINO oferuje:**

1. **Quantization (INT8/INT4)** — zmniejszenie rozmiaru modelu
2. **Pruning** — usunięcie zbędnych wag
3. **Knowledge Distillation** — trening mniejszego modelu
4. **Graph Optimization** — optymalizacja grafu obliczeń
5. **Auto-tuning** — automatyczne dopasowanie do hardware

---

## 4. Architektura rozwiązania

### Dla Linux + AMD (CPU + iGPU)

```
┌─────────────────────────────────────────────────────────┐
│ Aplikacja Desktopowa (Python/Qt)                        │
├─────────────────────────────────────────────────────────┤
│ OpenVINO Runtime API                                     │
│  ├─ Core                                                 │
│  ├─ CompiledModel                                        │
│  └─ InferRequest                                         │
├─────────────────────────────────────────────────────────┤
│ Execution Device                                         │
│  ├─ CPU (AMD Ryzen) — główny                            │
│  └─ GPU (AMD Radeon iGPU) — akceleracja                 │
├─────────────────────────────────────────────────────────┤
│ Model TranslateGemma (IR format)                        │
│  ├─ model.xml (architektura)                            │
│  └─ model.bin (wagi)                                    │
└─────────────────────────────────────────────────────────┘
```

### Przepływ danych:

```
Tekst wejściowy
    ↓
Tokenizer (Transformers)
    ↓
Input tensor (numpy)
    ↓
OpenVINO InferRequest
    ├─ CPU: AMD Ryzen (wielowątkowość)
    └─ GPU: AMD Radeon iGPU (równoległe obliczenia)
    ↓
Output tensor (logits)
    ↓
Detokenizer
    ↓
Tekst przetłumaczony
```

---

## 5. Implementacja krok po kroku

### 5.1 Instalacja OpenVINO

```bash
# Podstawowa instalacja
pip install openvino openvino-dev

# Dodatkowe narzędzia (opcjonalnie)
pip install openvino-tools

# Sprawdź instalację
python -c "import openvino; print(f'OpenVINO version: {openvino.__version__}')"
```

### 5.2 Gotowe modele OpenVINO (REKOMENDOWANE)

**✅ NAJŁATWIEJSZA OPCJA — użyj gotowego modelu OpenVINO INT8!**

#### Dostępny model:

| Model | Format | Kwantyzacja | Rozmiar | Pobrania | Link |
|-------|--------|-------------|---------|----------|------|
| **light434/translategemma-4b-it-int8-ov** | OpenVINO IR | INT8 (NNCF) | ~4.3 GB | 305 | [HuggingFace](https://huggingface.co/light434/translategemma-4b-it-int8-ov) |

#### Szczegóły modelu:

**Pliki:**
- `openvino_language_model.xml` / `.bin` — model językowy INT8 (~3.7 GB)
- `openvino_text_embeddings_model.xml` / `.bin` — text embeddings INT8 (~641 MB)
- `openvino_vision_embeddings_model.xml` / `.bin` — stub (nie SigLIP)
- Tokenizer / detokenizer IR

**Charakterystyka:**
- ✅ **Text-only** (bez tłumaczenia obrazów)
- ✅ **INT8 kwantyzacja** (mniejszy RAM, szybsza inferencja)
- ✅ **Gotowy do użycia** (nie trzeba konwertować)
- ✅ **OpenVINO GenAI** (VLMPipeline)
- ⚠️ **Nieoficjalny** (konwersja społeczności, nie Google)

#### Szybki start z gotowym modelem:

```bash
# 1. Zainstaluj zależności
pip install huggingface_hub openvino openvino-genai

# 2. Pobierz gotowy model OpenVINO INT8
huggingface-cli download light434/translategemma-4b-it-int8-ov \
    --local-dir ./models/translategemma-4b-it-int8-ov
```

#### Przykład użycia z gotowym modelem:

```python
import openvino_genai as ov_genai

# Załaduj gotowy model OpenVINO INT8
pipe = ov_genai.VLMPipeline("./models/translategemma-4b-it-int8-ov", "CPU")

# Ustaw chat template
pipe.set_chat_template("{{ bos_token }}{{ messages[-1]['content'] }}")

# Przygotuj prompt tłumaczenia
text = "Hello, how are you today?"
prompt = (
    "<start_of_turn>user\n"
    "You are a professional English (en) to Polish (pl) translator. "
    "Your goal is to accurately convey the meaning and nuances of the original English text "
    "while adhering to Polish grammar, vocabulary, and cultural sensitivities.\n"
    "Produce only the Polish translation, without any additional explanations or commentary. "
    "Please translate the following English text into Polish:\n\n\n"
    f"{text}"
    "<end_of_turn>\n"
    "<start_of_turn>model\n"
)

# Konfiguracja generowania
cfg = pipe.get_generation_config()
cfg.max_new_tokens = 512
cfg.max_length = 2048 + 512
cfg.do_sample = False
cfg.apply_chat_template = False
cfg.stop_token_ids = {1, 106}  # <eos>, <end_of_turn> — WAŻNE!

# Generuj tłumaczenie
translation = pipe.generate(prompt, generation_config=cfg)
print(f"PL: {translation}")
# Output: "Cześć, jak się dzisiaj masz?"
```

#### Oczekiwana wydajność (gotowy model INT8):

| Urządzenie | RAM | Czas (2000 znaków) | Uwagi |
|------------|-----|-------------------|-------|
| **CPU** (AMD Ryzen) | ~6 GB | ~15-25s | ✅ Rekomendowane |
| **GPU** (Intel iGPU) | ~4 GB | ~10-15s | ✅ Najszybsze |
| **GPU** (AMD iGPU) | ~4 GB | ~15-25s | ⚠️ Eksperymentalne |

#### Ważne uwagi dla gotowego modelu:

1. **Text-only** — model nie obsługuje tłumaczenia obrazów (vision stub)
2. **Stop tokens** — musisz ustawić `stop_token_ids = {1, 106}` inaczej generuje do max_new_tokens
3. **Nie przekazuj `images=[]`** — może spowodować OOM
4. **Chat template** — użyj passthrough template + ręcznie sformatowany prompt
5. **Nie konwertuj ponownie** — model jest już gotowy do użycia!

#### Porównanie: Gotowy model vs konwersja własna

| Opcja | Czas przygotowania | RAM | Wydajność | Rekomendacja |
|-------|-------------------|-----|-----------|--------------|
| **Gotowy model INT8** | 5 minut (pobranie) | ~6 GB | ⭐⭐⭐⭐⭐ | ✅ **NAJLEPSZE** |
| **Własna konwersja FP32** | 30 minut (konwersja) | ~12 GB | ⭐⭐⭐⭐ | ⚠️ Tylko jeśli potrzebujesz FP32 |
| **Własna konwersja INT8** | 60 minut (quantization) | ~6 GB | ⭐⭐⭐⭐⭐ | ⚠️ Niepotrzebne (masz gotowy) |

### 5.3 Pobranie i konwersja modelu (alternatywa)

**Użyj tej metody TYLKO jeśli nie możesz użyć gotowego modelu INT8!**

**Krok 1: Pobierz model ONNX**
```bash
# Pobierz model ONNX TranslateGemma 4B
huggingface-cli download onnx-community/translategemma-text-4b-it-ONNX \
    --local-dir ./models/onnx
```

**Krok 2: Konwertuj do formatu IR**
```bash
# Konwersja ONNX → IR (XML + BIN)
ovc --input_model ./models/onnx/model.onnx \
    --output_dir ./models/openvino \
    --compress_to_fp16

# Wynik:
# ./models/openvino/model.xml (architektura)
# ./models/openvino/model.bin (wagi, FP16)
```

**Krok 3: Quantization do INT8 (opcjonalne, dla mniejszego RAM)**
```bash
# Quantization INT8
pot -q default \
    --config quantization_config.json \
    --output-dir ./models/openvino_int8

# quantization_config.json:
# {
#     "model": {
#         "model_name": "translategemma",
#         "model": "./models/openvino/model.xml",
#         "weights": "./models/openvino/model.bin"
#     },
#     "engine": {
#         "config": {
#             "device": "CPU"
#         }
#     },
#     "dataset": {
#         "name": "default"
#     },
#     "quantization": {
#         "algorithms": [
#             {
#                 "name": "DefaultQuantization",
#                 "params": {
#                     "preset": "performance",
#                     "stat_subset_size": 300
#                 }
#             }
#         ]
#     }
# }
```

### 5.3 Podstawowa klasa tłumacza z OpenVINO

```python
from openvino.runtime import Core, InferRequest
from transformers import AutoTokenizer
import numpy as np
from typing import Optional

class TranslateGemmaOpenVINO:
    """Klasa do tłumaczenia przy pomocy TranslateGemma i OpenVINO."""
    
    def __init__(
        self,
        model_dir: str,
        device: str = "AUTO"  # "CPU", "GPU", "AUTO", "MULTI:CPU,GPU"
    ):
        """
        Inicjalizuj tłumacz OpenVINO.
        
        Args:
            model_dir: Ścieżka do katalogu z modelem IR (XML + BIN)
            device: Urządzenie ("CPU", "GPU", "AUTO", "MULTI:CPU,GPU")
        """
        # Inicjalizuj OpenVINO Core
        self.core = Core()
        
        # Sprawdź dostępne urządzenia
        available_devices = self.core.available_devices
        print(f"Dostępne urządzenia: {available_devices}")
        
        # Załaduj model IR
        model_path = f"{model_dir}/model.xml"
        self.model = self.core.read_model(model_path)
        
        # Kompiluj model dla wybranego urządzenia
        self.compiled_model = self.core.compile_model(self.model, device)
        self.infer_request = self.compiled_model.create_infer_request()
        
        # Załaduj tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            "google/translategemma-4b-it"
        )
        
        # Pobierz info o input/output
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        
        print(f"Model załadowany na urządzenie: {device}")
        print(f"Input shape: {self.input_layer.shape}")
        print(f"Output shape: {self.output_layer.shape}")
    
    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "pl",
        max_new_tokens: int = 512
    ) -> str:
        """
        Przetłumacz tekst.
        
        Args:
            text: Tekst do tłumaczenia
            source_lang: Kod języka źródłowego (ISO 639-1)
            target_lang: Kod języka docelowego (ISO 639-1)
            max_new_tokens: Maksymalna liczba tokenów w wyjściu
        
        Returns:
            Przetłumaczony tekst
        """
        # Przygotuj wiadomości w formacie TranslateGemma
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text,
                        "source_lang_code": source_lang,
                        "target_lang_code": target_lang
                    }
                ]
            }
        ]
        
        # Aplikuj chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False
        )
        
        # Tokenizuj input
        inputs = self.tokenizer(
            prompt,
            return_tensors="np",
            padding=True,
            truncation=True,
            max_length=4096
        )
        
        input_ids = inputs["input_ids"].astype(np.int32)
        
        # Generuj tłumaczenie (autoregressive decoding)
        generated_ids = input_ids.copy()
        
        for _ in range(max_new_tokens):
            # Uruchom inferencję
            self.infer_request.infer({self.input_layer: generated_ids})
            
            # Pobierz output (logits)
            output = self.infer_request.get_tensor(self.output_layer)
            logits = output.data
            
            # Pobierz next token (greedy decoding)
            next_token_logits = logits[:, -1, :]
            next_token = np.argmax(next_token_logits, axis=-1, keepdims=True)
            
            # Dodaj do wygenerowanych tokenów
            generated_ids = np.concatenate([generated_ids, next_token], axis=1)
            
            # Sprawdź czy EOS token
            if next_token[0, 0] == self.tokenizer.eos_token_id:
                break
        
        # Dekoduj wynik
        translation = self.tokenizer.decode(
            generated_ids[0, input_ids.shape[1]:],
            skip_special_tokens=True
        )
        
        return translation
```

### 5.4 Użycie tłumacza

```python
# Inicjalizuj tłumacz z OpenVINO
translator = TranslateGemmaOpenVINO(
    model_dir="./models/openvino",
    device="AUTO"  # Automatyczny wybór CPU/GPU
)

# Przykład 1: Angielski → Polski
translation = translator.translate(
    text="Hello, how are you today?",
    source_lang="en",
    target_lang="pl"
)
print(f"PL: {translation}")

# Przykład 2: Z wymuszeniem CPU
translator_cpu = TranslateGemmaOpenVINO(
    model_dir="./models/openvino",
    device="CPU"
)

# Przykład 3: Z wymuszeniem GPU (iGPU AMD)
translator_gpu = TranslateGemmaOpenVINO(
    model_dir="./models/openvino",
    device="GPU"
)
```

### 5.5 Benchmark dla różnych urządzeń

```python
import time

def benchmark_translation(translator, text: str, runs: int = 5):
    """Benchmark tłumaczenia."""
    times = []
    
    for i in range(runs):
        start = time.time()
        result = translator.translate(text, source_lang="en", target_lang="pl")
        end = time.time()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    print(f"Średni czas: {avg_time:.2f}s")
    print(f"Min: {min(times):.2f}s, Max: {max(times):.2f}s")
    
    return avg_time

# Test na CPU
print("=== CPU (AMD Ryzen) ===")
benchmark_translation(translator_cpu, "Hello world")

# Test na GPU (iGPU AMD)
print("\n=== GPU (AMD Radeon iGPU) ===")
benchmark_translation(translator_gpu, "Hello world")

# Test na AUTO
print("\n=== AUTO (wybór OpenVINO) ===")
benchmark_translation(translator, "Hello world")
```

### 5.6 Integracja z PyQt6

```python
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTextEdit, QPushButton, QComboBox, QLabel, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal

class TranslationWorker(QThread):
    """Worker thread do tłumaczenia z OpenVINO."""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, translator, text, source_lang, target_lang):
        super().__init__()
        self.translator = translator
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
    
    def run(self):
        try:
            result = self.translator.translate(
                self.text,
                self.source_lang,
                self.target_lang
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class TranslatorApp(QMainWindow):
    """Główne okno aplikacji z OpenVINO."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TranslateGemma Desktop (OpenVINO)")
        self.setGeometry(100, 100, 800, 600)
        
        # Inicjalizuj tłumacz OpenVINO
        print("Ładowanie modelu OpenVINO...")
        self.translator = TranslateGemmaOpenVINO(
            model_dir="./models/openvino",
            device="AUTO"  # lub "CPU" / "GPU"
        )
        print("Model załadowany!")
        
        # UI
        self.init_ui()
    
    def init_ui(self):
        """Inicjalizuj interfejs użytkownika."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Label
        layout.addWidget(QLabel("Tekst źródłowy:"))
        
        # Input text
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Wpisz tekst do tłumaczenia...")
        layout.addWidget(self.input_text)
        
        # Language selection
        lang_layout = QVBoxLayout()
        
        self.source_lang = QComboBox()
        self.source_lang.addItems(["auto", "en", "de", "fr", "es", "it", "ru", "uk"])
        lang_layout.addWidget(QLabel("Język źródłowy:"))
        lang_layout.addWidget(self.source_lang)
        
        self.target_lang = QComboBox()
        self.target_lang.addItems(["pl", "en", "de", "fr", "es", "it", "ru", "uk"])
        lang_layout.addWidget(QLabel("Język docelowy:"))
        lang_layout.addWidget(self.target_lang)
        
        layout.addLayout(lang_layout)
        
        # Translate button
        self.translate_btn = QPushButton("Tłumacz (OpenVINO)")
        self.translate_btn.clicked.connect(self.start_translation)
        layout.addWidget(self.translate_btn)
        
        # Output text
        layout.addWidget(QLabel("Tłumaczenie:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
    
    def start_translation(self):
        """Rozpocznij tłumaczenie."""
        text = self.input_text.toPlainText()
        if not text:
            return
        
        self.translate_btn.setEnabled(False)
        self.translate_btn.setText("Tłumaczę...")
        
        # Uruchom worker thread
        self.worker = TranslationWorker(
            self.translator,
            text,
            self.source_lang.currentText(),
            self.target_lang.currentText()
        )
        self.worker.finished.connect(self.on_translation_finished)
        self.worker.error.connect(self.on_translation_error)
        self.worker.start()
    
    def on_translation_finished(self, result: str):
        """Obsługa zakończenia tłumaczenia."""
        self.output_text.setPlainText(result)
        self.translate_btn.setEnabled(True)
        self.translate_btn.setText("Tłumacz (OpenVINO)")
    
    def on_translation_error(self, error: str):
        """Obsługa błędu."""
        self.output_text.setPlainText(f"Błąd: {error}")
        self.translate_btn.setEnabled(True)
        self.translate_btn.setText("Tłumacz (OpenVINO)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorApp()
    window.show()
    sys.exit(app.exec())
```

---

## 6. Optymalizacja dla zintegrowanego GPU AMD

### 6.1 Sprawdź czy iGPU jest dostępne

```bash
# Sprawdź czy masz zintegrowane GPU AMD
lspci | grep -i vga

# Powinieneś zobaczyć coś jak:
# "Advanced Micro Devices [AMD/ATI] Raven Ridge [Radeon Vega Series]"
# lub
# "Advanced Micro Devices [AMD/ATI] Renoir [Radeon Graphics]"

# Sprawdź czy OpenVINO widzi GPU
python -c "
from openvino.runtime import Core
core = Core()
print('Dostępne urządzenia:', core.available_devices)
# Powinieneś zobaczyć: ['CPU', 'GPU.0']
"
```

### 6.2 Konfiguracja dla iGPU AMD

```python
from openvino.runtime import Core, properties

core = Core()

# Konfiguruj dla GPU (iGPU AMD)
config = {
    # Optymalizacje dla GPU
    properties.hint.performance_mode: properties.hint.PerformanceMode.LATENCY,
    properties.hint.num_requests: "1",
    
    # Precyzja obliczeń
    properties.inference_num_threads: "4",
    
    # Cache
    properties.cache_dir: "./openvino_cache"
}

# Kompiluj model z konfiguracją
compiled_model = core.compile_model(
    model,
    device_name="GPU",
    config=config
)
```

### 6.3 Multi-device: CPU + GPU

```python
# Użyj zarówno CPU jak i GPU jednocześnie
compiled_model = core.compile_model(
    model,
    device_name="MULTI:CPU,GPU"
)

# OpenVINO automatycznie rozdzieli obciążenie
# pomiędzy CPU (AMD Ryzen) i GPU (Radeon iGPU)
```

### 6.4 Benchmark: CPU vs GPU vs MULTI

```python
import time

def benchmark_device(device_name: str, runs: int = 10):
    """Benchmark dla różnych urządzeń."""
    translator = TranslateGemmaOpenVINO(
        model_dir="./models/openvino",
        device=device_name
    )
    
    text = "The quick brown fox jumps over the lazy dog."
    times = []
    
    for _ in range(runs):
        start = time.time()
        translator.translate(text, source_lang="en", target_lang="pl")
        end = time.time()
        times.append(end - start)
    
    avg = sum(times) / len(times)
    print(f"{device_name:15s}: {avg:.2f}s (±{max(times)-min(times):.2f}s)")

# Testuj różne konfiguracje
print("=== Benchmark TranslateGemma na AMD ===\n")
benchmark_device("CPU")
benchmark_device("GPU")
benchmark_device("AUTO")
benchmark_device("MULTI:CPU,GPU")
```

**Oczekiwane wyniki dla AMD Ryzen + Radeon Vega:**

| Urządzenie | Czas (2000 znaków) | RAM | Uwagi |
|------------|-------------------|-----|-------|
| **CPU** (Ryzen 7) | ~25-40s | ~12 GB | Stabilne |
| **GPU** (Vega iGPU) | ~15-25s | ~4 GB (shared) | **Szybsze!** |
| **AUTO** | ~15-25s | ~4-12 GB | Wybiera GPU |
| **MULTI:CPU,GPU** | ~12-20s | ~12 GB | Najszybsze |

---

## 7. Porównanie wydajności

### 7.1 OpenVINO vs ONNX Runtime na AMD

| Rozwiązanie | CPU (AMD) | GPU (iGPU) | RAM | Łatwość |
|-------------|-----------|------------|-----|---------|
| **OpenVINO** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **ONNX Runtime** | ⭐⭐⭐ | ⭐⭐ (ROCm) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### 7.2 Oczekiwana wydajność

**Dla AMD Ryzen 7 + Radeon Vega (iGPU):**

| Model | Urządzenie | Czas (2000 znaków) | RAM |
|-------|------------|-------------------|-----|
| **TranslateGemma 4B (FP32)** | CPU | ~25-40s | ~12 GB |
| **TranslateGemma 4B (FP32)** | GPU (iGPU) | ~15-25s | ~4 GB (shared) |
| **TranslateGemma 4B (INT8)** | CPU | ~15-25s | ~6 GB |
| **TranslateGemma 4B (INT8)** | GPU (iGPU) | ~10-15s | ~3 GB (shared) |

---

## 8. Rozwiązywanie problemów

### 8.1 Typowe błędy

**Błąd: "GPU device not found"**
```bash
# Sprawdź czy iGPU jest widoczne
lspci | grep -i vga

# Zainstaluj sterowniki AMD
sudo apt install mesa-vulkan-drivers

# Sprawdź czy OpenVINO widzi GPU
python -c "from openvino.runtime import Core; print(Core().available_devices)"
```

**Błąd: "Model requires more memory than available"**
```python
# Rozwiązanie: Użyj quantization INT8
# Lub użyj CPU zamiast GPU (więcej RAM)
translator = TranslateGemmaOpenVINO(
    model_dir="./models/openvino_int8",  # INT8 model
    device="CPU"
)
```

**Błąd: "OpenVINO runtime error"**
```bash
# Sprawdź wersję OpenVINO
python -c "import openvino; print(openvino.__version__)"

# Aktualizuj OpenVINO
pip install --upgrade openvino openvino-dev
```

### 8.2 Debugowanie

```python
from openvino.runtime import Core

core = Core()

# Sprawdź dostępne urządzenia
print("Dostępne urządzenia:", core.available_devices)

# Sprawdź properties urządzenia
for device in core.available_devices:
    print(f"\n{device}:")
    print(f"  Name: {core.get_property(device, 'FULL_DEVICE_NAME')}")
    print(f"  Architecture: {core.get_property(device, 'DEVICE_ARCHITECTURE')}")
```

---

## 9. Podsumowanie

### OpenVINO vs ONNX Runtime — co wybrać?

| Kryterium | OpenVINO | ONNX Runtime |
|-----------|----------|--------------|
| **AMD CPU** | ✅ **NAJLEPSZE** | ✅ Dobre |
| **AMD iGPU** | ✅ **NAJLEPSZE** | ⚠️ Ograniczone (ROCm) |
| **Łatwość użycia** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Wydajność** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Dokumentacja** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### Rekomendacja dla Linux + AMD (wbudowane GPU):

**✅ Użyj OpenVINO gdy:**
- Masz AMD CPU (Ryzen) — najlepsze optymalizacje
- Masz zintegrowane GPU AMD (Radeon Vega/Renoir) — pełne wsparcie
- Chcesz maksymalnej wydajności na AMD hardware
- Potrzebujesz quantization i optymalizacji

**❌ Użyj ONNX Runtime gdy:**
- Potrzebujesz cross-platform (Windows/Linux/macOS)
- Masz NVIDIA GPU (CUDA)
- Chcesz prostszej integracji
- Nie chcesz konwertować modeli

### Szybki start dla Linux + AMD:

```bash
# 1. Zainstaluj OpenVINO
pip install openvino openvino-dev transformers

# 2. Pobierz i skonwertuj model
huggingface-cli download onnx-community/translategemma-text-4b-it-ONNX \
    --local-dir ./models/onnx

ovc --input_model ./models/onnx/model.onnx \
    --output_dir ./models/openvino \
    --compress_to_fp16

# 3. Sprawdź urządzenia
python -c "
from openvino.runtime import Core
core = Core()
print('Dostępne:', core.available_devices)
"

# 4. Uruchom tłumaczenie
python translate_example.py
```

### Oczekiwana wydajność:

**AMD Ryzen 7 + Radeon Vega (iGPU):**
- **CPU only:** ~25-40s per 2000 znaków
- **GPU (iGPU):** ~15-25s per 2000 znaków ← **REKOMENDOWANE**
- **MULTI:CPU,GPU:** ~12-20s per 2000 znaków ← **NAJSZYBSZE**

---

**Ostatnia aktualizacja:** 2026-09-06  
**Status:** Kompletny przewodnik dla Linux + AMD  
**Wersja:** 1.0
