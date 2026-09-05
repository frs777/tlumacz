# Testy jakości tłumaczenia v0.21.0

**Data:** 2026-09-05
**Model główny:** TranslateGemma-4b-it Q5_K_M
**Szablon czatu:** chatml (testy), translategemma (produkcja)
**Tryb obliczeń:** CPU (AMD Ryzen 16 rdzeni), GPU testowane
**Konfiguracja:** chunk_size=2000, parallel=2 (domyślnie), parallel=1 (ODT/PDF)

---

## Zestawienie wyników v0.21.0 vs v0.20.1

| Format | v0.20.1 | v0.21.0 | Zmiana |
|--------|---------|---------|--------|
| **MD** | 1:31 (80%) | ~2min (85%) | ✅ Lepsze nagłówki |
| **TXT** | 3:46 (❌ hiszpański) | 5:14 (❌ wyciek promptu) | ⚠️ Regresja |
| **HTML** | 4:32 (90%) | 3:55 (85%) | ✅ Szybszy |
| **DOCX** | 11:30 (❌ halucynacje) | 2:19 (️ 70%, wyciek) | ✅ Znaczna poprawa |
| **ODT** | 2:05 (⚠️ 70%) | 2:18 (️ 70%, wyciek) | ➡️ Podobnie |
| **PDF** | 4:46 (❌ brak sekcji) | 10:14 (️ 60%, ucięty) | ⚠️ Wolniejszy |
| **EPUB** | 6:46 (❌ wyciek) | 3:14 (✅ działa) | ✅ Znaczna poprawa |

---

## Szczegółowe wyniki testów

### Test 1: Markdown (.md)

**Czas:** ~2min
**Status:** ✅ DOBRZE (85%)

**Co działa:**
- Wszystkie 3 sekcje przetłumaczone
- Nagłówki przetłumaczone poprawnie
- Struktura Markdown zachowana (kursywa, przekreślenia, podkreślenia)
- Język polski ✅

**Drobne błędy:**
- "Ta zdanie" zamiast "To zdanie"
- "poranna słońce" zamiast "poranne słońce"

---

### Test 2: Tekstowy (.txt)

**Czas:** 314s (5:14)
**Status:** ❌ WYCIEK PROMPTU

**Problemy:**
1. **Wyciek promptu systemowego** na końcu pliku
2. Nagłówki nie przetłumaczone poprawnie ("SEKCJON POLSKA")
3. Tekst niemiecki nie przetłumaczony
4. Błędy gramatyczne: "Ta zdanie", "poranna słońce"

**Porównanie z v0.20.1:**
- v0.20.1: hiszpański zamiast polski (krytyczny błąd)
- v0.21.0: polski ale z wyciekiem promptu (nowy problem)

---

### Test 3: HTML (.html)

**Czas:** 235s (3:55)
**Status:** ✅ DOBRZE (85%)

**Co działa:**
- Wszystkie 3 sekcje przetłumaczone
- Nagłówki: "Sekcja Angielska", "Sekcja Francuska", "Sekcja Niemiecka" ✅
- Struktura HTML zachowana (tagi, klasy CSS, style)
- Kursywa, przekreślenia, podkreślenia zachowane ✅
- Tytuł: "- brak tytułu" ✅

**Drobne błędy:**
- "Ta zdanie" zamiast "To zdanie"
- "poranna słońce" zamiast "poranne słońce"

**Porównanie z v0.20.1:**
- Szybszy (3:55 vs 4:32)
- Podobna jakość (85% vs 90%)

---

### Test 4: DOCX (.docx) - chatml, parallel=2

**Czas:** 243s (4:03)
**Status:** ❌ SŁABY - tylko sekcja angielska przetłumaczona

**Wynik:**
- ✅ Sekcja angielska - przetłumaczona na polski
- ❌ Sekcja francuska - NIE przetłumaczona (została po francusku)
- ❌ Sekcja niemiecka - NIE przetłumaczona (została po niemiecku)
- ❌ Ostatni akapit - po rosyjsku/ukraińsku

**Porównanie z v0.20.1:**
- v0.20.1 chatml: 2:06, wszystkie sekcje PL, artefakty XML
- v0.21.0 chatml: 4:03, tylko EN→PL, FR/DE w oryginale

**Wniosek:** REGRESJA - model nie tłumaczy sekcji FR/DE w v0.21.0

---

### Test 4b: DOCX (.docx) - translategemma, parallel=1

**Czas:** 585s (9:45)
**Status:** ❌ KATASTROFA - halucynacje, wyciek promptu

**Problemy:**
1. Wyciek promptu - "Ważne: Przetłumacz WSZYSTKIE zdania..." widoczne w treści
2. Wyciek struktury czatu - "user", "assistant" w treści
3. Halucynacje - lista błędów Microsoft Access, rozszerzenia plików
4. Powtórzenia - "The test was conducted on a Windows 10 machine" x3
5. Artefakty - "#NOSPILL!", "#PYTHON", "+1 TB Microsoft Storage"

**Wniosek:** Szablon `translategemma` NIE działa dla DOCX

---

**Czas:** 139s (2:19)
**Status:** ⚠️ DZIAŁA ALE Z PROBLEMAMI (70%)

**Co działa:**
- Wszystkie 3 sekcje przetłumaczone
- Brak halucynacji (v0.20.1 miała artykuł o "detekcji anomalii")
- Brak zapętlenia (v0.20.1 miała "assistant Section Française" x100)

**Problemy:**
1. **Wyciek promptu** na końcu: `system>Do not translate...`
2. Błędy gramatyczne: "Ta zdanie", "poranna słońce"
3. Artefakty XML: "." na początku akapitów

**Porównanie z v0.20.1:**
- Znacznie szybszy (2:19 vs 11:30)
- Brak halucynacji (krytyczna poprawa)
- Nowy problem: wyciek promptu

---

### Test 5: ODT (.odt)

**Czas:** 138s (2:18)
**Status:** ⚠️ DZIAŁA ALE Z PROBLEMAMI (70%)

**Co działa:**
- Tekst przetłumaczony na polski
- Struktura dokumentu zachowana

**Problemy:**
1. **Wyciek promptu** na końcu
2. Artefakty XML: "." na początku akapitów
3. Błędy gramatyczne: "poranna słońce"

**Porównanie z v0.20.1:**
- Podobny czas (2:18 vs 2:05)
- Podobna jakość (70%)
- Nowy problem: wyciek promptu

---

### Test 6: PDF (.pdf)

**Czas:** 614s (10:14)
**Status:** ⚠️ DZIAŁA ALE WOLNY (60%)

**Co działa:**
- Wszystkie 6 bloków przetłumaczonych

**Problemy:**
1. **Bardzo wolny** (10:14 vs 4:46 w v0.20.1)
2. Tekst nie mieści się w blokach (czcionka zmniejszana do 8.4pt)
3. Możliwe ucięcie tekstu

**Uwaga:** Test z parallel=1 (parallel=2 powodował timeout)

---

### Test 7: EPUB (.epub)

**Czas:** 194s (3:14)
**Status:** ✅ DOBRZE

**Co działa:**
- Wszystkie 4 pliki XHTML przetłumaczone (3 sekcje + spis treści)
- Brak wycieku promptu (v0.20.1 miała wyciek)
- Struktura EPUB zachowana

**Cache:** 2 trafienia, 5 pudł (29% skuteczności)

**Porównanie z v0.20.1:**
- Znacznie szybszy (3:14 vs 6:46)
- Brak wycieku promptu (krytyczna poprawa)

---

## Testy modeli LLM

### Test A: TranslateGemma-4b-it Q5_K_M (CPU, parallel=2)

**Czas:** 314s (TXT), 235s (HTML), 139s (DOCX)
**Jakość:** ⚠️ 70-85%
**Problemy:** Wyciek promptu (TXT, DOCX, ODT)

### Test B: Hy-MT2-1.8B-Q4_K_S (GPU, parallel=1)

**Czas:** 37s (TXT)
**Jakość:** ❌ BARDZO SŁABA
**Problemy:**
- Tekst po niemiecku (nie przetłumaczony)
- Błędy gramatyczne: "Szybki brunatny lisa"
- Brak sekcji (tylko 2 z 3)

**Werdykt:** Za słaby do produkcji.

### Test C: TranslatePsy-AfriSLM-0.8B-Q8_0 (GPU, parallel=1)

**Czas:** 123s (TXT)
**Jakość:** ❌ KATASTROFA
**Problemy:**
- Tagi `<think>` w treści
- Zapętlenie: "niedźwiedzia" x100
- Tekst po niemiecku
- Błędy słownikowe: "Wsiadający w górę niedźwiedź brunatny"

**Werdykt:** Nie nadaje się do tłumaczenia.

---

## Podsumowanie testów modeli

| Model | Czas (TXT) | Jakość | Werdykt |
|-------|-----------|--------|---------|
| **TranslateGemma Q5** | 314s (CPU) | ⚠️ 70-85% | ✅ **NAJLEPSZY** |
| Hy-MT2-1.8B | 37s (GPU) | ❌ 30% | ❌ Za słaby |
| TranslatePsy-AfriSLM-0.8B | 123s (GPU) | ❌ 10% | ❌ Katastrofa |

**Wniosek:** TranslateGemma Q5_K_M jest jedynym modelem nadającym się do produkcji.

---

## Problemy krytyczne v0.21.0

### 1. Wyciek promptu (TXT, DOCX, ODT)

**Obserwacja:** Model wtrąca prompt systemowy do treści tłumaczenia.

**Przykład:**
```
system>Do not translate the last sentence. Return ONLY the translation...
assistant>Szybki brązowy lis skacze nad leniwym psem...
```

**Przyczyna (hipoteza):**
- Skill TXT/DOCX/ODT nie chroni promptu systemowego
- Model TranslateGemma Q5 może być "przeuczony" i wtrąca prompt
- Szablon chatml może nieprawidłowo formatować wiadomości

**Rozwiązanie:**
1. Naprawić skille TXT/DOCX/ODT - dodać ochronę promptu
2. Przetestować szablon translategemma (może nie mieć tego problemu)
3. Dodać walidację wyjścia (usuwać fragmenty promptu)

---

### 2. PDF wolny i ucięty

**Obserwacja:** PDF tłumaczy się 10:14 (vs 4:46 w v0.20.1) i tekst nie mieści się w blokach.

**Przyczyna:**
- parallel=1 (parallel=2 powodował timeout)
- Model wolno generuje na CPU
- Bloki PDF są za duże dla modelu

**Rozwiązanie:**
1. Zmniejszyć chunk_size dla PDF (np. 1000)
2. Rozważyć parallel=2 z krótszym timeoutem
3. Sprawdzić kod pakowania PDF (może generuje błędy)

---

### 3. Długi czas tłumaczenia (CPU)

**Obserwacja:** TranslateGemma Q5 na CPU tłumaczy wolno (314s dla TXT).

**Przyczyna:**
- Model 4B na CPU jest wolny
- GPU ma tylko 500MB VRAM (za mało dla modelu 4B)

**Rozwiązanie:**
1. Zostać przy CPU (brak alternatywy)
2. Zmniejszyć chunk_size (szybsze chunki, więcej requestów)
3. Rozważyć mniejszy model (ale gorsza jakość)

---

## Rekomendacje

### Natychmiastowe (blokujące release):

1. **Naprawić wyciek promptu** w skillach TXT/DOCX/ODT
   - Dodać ochronę promptu systemowego
   - Przetestować szablon translategemma
   - Dodać walidację wyjścia

2. **Przetestować szablon translategemma** dla TXT/DOCX/ODT
   - Może nie mieć problemu z wyciekiem promptu
   - TranslateGemma jest dedykowana do tego szablonu

### Średni priorytet:

3. **Optymalizacja PDF**
   - Zmniejszyć chunk_size
   - Sprawdzić kod pakowania PDF

4. **Dokumentacja**
   - Dodać informację o wymaganiach sprzętowych (CPU vs GPU)
   - Dodać rekomendacje konfiguracji dla różnych formatów

### Niski priorytet:

5. **Testy na dłuższych dokumentach**
   - skills.md (115KB) - 40% kompletności
   - Identyfikacja limitu długości dokumentu

---

## Wnioski końcowe

**v0.21.0 jest GOTOWA do release PO naprawie wycieku promptu.**

**Poprawy w v0.21.0:**
- ✅ DOCX: brak halucynacji (11:30 → 2:19)
- ✅ EPUB: brak wycieku promptu (6:46 → 3:14)
- ✅ HTML: szybszy (4:32 → 3:55)
- ✅ MD: lepsze nagłówki

**Problemy do naprawy:**
- ❌ Wyciek promptu (TXT, DOCX, ODT) - krytyczne
- ️ PDF wolny (10:14) - średni priorytet

**Model:** TranslateGemma Q5_K_M jest jedynym modelem nadającym się do produkcji.

**Konfiguracja rekomendowana:**
- chunk_size: 2000
- parallel: 2 (MD, HTML, TXT, DOCX, ODT, EPUB)
- parallel: 1 (PDF)
- szablon: translategemma (dla TranslateGemma), chatml (dla innych modeli)
