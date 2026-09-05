# Testy tłumaczenia v0.20.1 - Dokument 3-języczny

**Dokument testowy:** TEST3 (2000 znaków, 3 języki: EN, FR, DE → PL)  
**Data:** 2026-09-03

---

## Test 1: Plik tekstowy (.txt) - chunk_size=4000

**Czas tłumaczenia:** 1:12  
**Status:** ❌ NIEKOMPLETNE

### Wynik

Tłumaczenie jest **niekompletne** - przetłumaczony plik zawiera tylko fragment pierwszej sekcji i jest ucięty w środku zdania.

**Oryginał:** 3 sekcje (angielska, francuska, niemiecka) po ~150 słów każda  
**Tłumaczenie:** ~100 słów, ucięte po "nowoczesnym"

### Problemy

1. **Niekompletne tłumaczenie** - brak 2/3 dokumentu
2. **Ucięte zdanie** - "Technologia i nauka stale się szybko rozwijają w nowoczesnym" (brak końca)
3. **Nagłówek "SEKCJĘ POLSKĄ"** - powinien być "SEKCJA POLSKA" lub "SEKCJA ANGIELSKA" (błąd gramatyczny)

### Przykłady błędów

| Oryginał (EN) | Tłumaczenie (PL) | Problem |
|---------------|------------------|---------|
| "ENGLISH SECTION" | "SEKCJĘ POLSKĄ" | Zły nagłówek + błąd gramatyczny |
| "while the morning sun rises slowly" | "podczas gdy wschodzi słoneczne poranne" | Niegramatyczne |
| "This sentence contains common words" | "Ta zdanie zawiera powszechne słowa" | "Ta zdanie" → "To zdanie" |

### Diagnoza

Prawdopodobne przyczyny:
- Zbyt mały `chunk_size` - model nie mieści całego tekstu
- Problem z modelem LLM - ucinanie długich odpowiedzi
- Błąd w kodzie - nieprawidłowe łączenie bloków

---

## Test 1b: Plik tekstowy (.txt) - chunk_size=2000, parallel=1

**Czas tłumaczenia:** 3:46  
**Status:** ❌ KRYTYCZNY BŁĄD - ZŁY JĘZYK DOCLOWY

### Wynik

Model tłumaczy na **HISZPAŃSKI** zamiast na POLSKI! To krytyczny błąd.

### Problemy

1. **Zły język docelowy** - tłumaczenie na hiszpański zamiast polski
2. **Mieszanie języków** - sekcja niemiecka częściowo po niemiecku, częściowo po hiszpańsku
3. **Dodatkowa sekcja** - model dodał własną sekcję po polsku na końcu (halucynacja)
4. **Tagi HTML** - na końcu pliku出现了 `<|file1|>` do `<|file128|>` (artefakty)

### Przykłady błędów

| Oryginał (EN) | Tłumaczenie | Problem |
|---------------|-------------|---------|
| "ENGLISH SECTION" | "SECCIÓN EN INGLÉS" | Hiszpański zamiast polski! |
| "SECTION FRANÇAISE" | "SECCIÓN FRANCESA" | Hiszpański zamiast polski! |
| "DEUTSCHER ABSCHNITT" | "SECCIÓN ALEMANA" | Hiszpański zamiast polski! |

### Diagnoza

Prawdopodobne przyczyny:
- **Prompt systemowy nie działa** - model ignoruje "Translate to Polish"
- **Model przeuczony na hiszpański** - może być fine-tunowany na dane hiszpańskie
- **Problem z konfiguracją** - `target_language` może nie być przekazywane do promptu

### Rekomendacja

1. **Natychmiast sprawdzić prompt systemowy** - czy zawiera "Polish"?
2. **Sprawdzić konfigurację** - `target_language: "Polish"` w config.json
3. **Przetestować inny model** - ten model może być uszkodzony
4. **Dodać walidację języka** - wykrywać gdy tłumaczenie nie jest po polsku

---

## Test 2: Plik Markdown (.md) - chunk_size=2000, parallel=1

**Czas tłumaczenia:** 1:31  
**Status:** ✅ PRAWIE POPRAWNIE

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU** (w przeciwieństwie do testu TXT!). Struktura Markdown zachowana.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone
- Nagłówki `#` zachowane
- Kursywa `*...*` zachowana
- Przekreślenia `~~...~~` zachowane
- Podkreślenia `{.underline}` zachowane
- Język docelowy: POLSKI ✅

### ⚠️ Błędy gramatyczne (per sekcja)

**Sekcja angielska:**
| Oryginał | Tłumaczenie | Problem |
|----------|-------------|---------|
| "This sentence contains" | "Ta zdanie zawiera" | "To zdanie" |
| "while the morning sun rises slowly" | "podczas gdy wschodzi słoneczny poranek" | Niegramatyczne |

**Sekcja francuska:**
| Oryginał | Tłumaczenie | Problem |
|----------|-------------|---------|
| "Cette phrase contient" | "Ta zdanie zawiera" | "To zdanie" |
| "Le renard brun rapide saute par-dessus le chien paresseux" | "Lis brązowy skacze nad psem leniwym" | Dziwny szyk |

**Sekcja niemiecka:**
| Oryginał | Tłumaczenie | Problem |
|----------|-------------|---------|
| "Dieser Satz enthält" | "Ten zdanie zawiera" | "To zdanie" |
| "während die Morgensonne langsam über die fernen Hügel aufgeht" | "podczas gdy wschodzące słońce powoli wschodzi" | Powtórzenie "wschodzi" |

### Porównanie z testem TXT

| Test | Czas | Język | Kompletność | Jakość |
|------|------|-------|-------------|--------|
| TXT (chunk=4000) | 1:12 | PL | 30% | ❌ |
| TXT (chunk=2000) | 3:46 | ES | 100% | ❌ Zły język |
| MD (chunk=2000) | 1:31 | PL | 100% | ⚠️ 80% |

**Wniosek:** Skill Markdown poprawia jakość tłumaczenia! Prompt dla Markdown zawiera lepsze instrukcje.

---

## Test 3: Plik DOCX (.docx) - chunk_size=2000, parallel=1

**Czas tłumaczenia:** 11:30  
**Status:** ❌ KATASTROFA - HALUCYNACJE

### Wynik

Tłumaczenie jest **całkowicie zepsute**. Model wygenerował halucynacje i powtarzający się tekst.

### Problemy

1. **Obcy tekst na początku** - model dodał artykuł o "detekcji anomalii w danych szeregów czasowych" (autor: Jan Kowalski) - kompletna halucynacja
2. **Sekcja francuska** - powtarzający się tekst "assistant Section Française" (setki razy!)
3. **Sekcja niemiecka** - NIE ISTNIEJE w tłumaczeniu
4. **Czas tłumaczenia** - 11:30 (bardzo długo, model się zapętlił)

### Przykład halucynacji

```
<|file_name|>document.docx <|document|> --- Tytuł: Analiza porównawcza różnych metod detekcji anomalii w danych szeregów czasowych. Autor: Jan Kowalski Data: 2023-10-27...
```

### Przykład zapętlenia

```
Sekcja Francuska assistant Section Française assistant Section Française assistant Section Française...
```

### Diagnoza

- Model nie radzi sobie z formatem DOCX
- Skill DOCX może być uszkodzony lub niekompatybilny
- Model gubi kontekst i generuje losowy tekst

### Porównanie formatów

| Test | Format | Czas | Język | Kompletność | Jakość |
|------|--------|------|-------|-------------|--------|
| 1 | .txt (chunk=4000) | 1:12 | PL | 30% | ❌ |
| 1b | .txt (chunk=2000) | 3:46 | ES | 100% | ❌ Zły język |
| 2 | .md (chunk=2000) | 1:31 | PL | 100% | ⚠️ 80% |
| 3 | .docx (chunk=2000) | 11:30 | PL | 50% | ❌ Halucynacje |

---

## Test 4: Plik ODT (.odt) - chunk_size=2000, parallel=1

**Czas tłumaczenia:** 2:05  
**Status:** ⚠️ DZIAŁA ALE Z PROBLEMAMI

### Wynik

Tłumaczenie jest **kompletne** (wszystkie 3 sekcje), ale z artefaktami XML i błędami gramatycznymi.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Język polski ✅
- Struktura dokumentu zachowana

### ⚠️ Problemy

1. **Artefakty XML na początku:**
   ```
   <|tag_separator|>
   <|section_separator|>
   <|table_separator|>
   <|cell_separator|>
   <|row_separator|>
   <|column_separator|>
   ```

2. **Błędy gramatyczne:**
   - "Ta zdanie" zamiast "To zdanie" (we wszystkich sekcjach)
   - "poranna słońce" zamiast "poranne słońce"
   - "łatwo tłumaczyć się" (dziwny szyk)

3. **Błędy tłumaczenia:**
   - Sekcja DE: "oświetla dolinę" (w oryginale jest o wzgórzach, nie dolinie!)

4. **Formatowanie:**
   - Sekcja FR podzielona na wiele akapitów (może problem z XML)

### Porównanie formatów binarnych

| Format | Czas | Język | Kompletność | Jakość |
|--------|------|-------|-------------|--------|
| DOCX | 11:30 | PL | 50% | ❌ Halucynacje |
| ODT | 2:05 | PL | 100% | ⚠️ 70% |

**Wniosek:** ODT działa lepiej niż DOCX, ale nadal ma problemy z artefaktami XML.

---

## Test 5: Plik PDF (.pdf) - chunk_size=2000, parallel=1

**Czas tłumaczenia:** 4:46  
**Status:** ❌ NIEKOMPLETNE - BRAK SEKCJI

### Wynik

Tłumaczenie jest **niekompletne** - brakuje nagłówków sekcji i całej sekcji angielskiej!

### Problemy

1. **Brak nagłówków** - "English Section", "Section Française", "Deutscher Abschnitt" nie zostały przetłumaczone
2. **Brak sekcji angielskiej** - pierwszy akapit tekstu to tłumaczenie sekcji francuskiej!
3. **Tekst ucięty** - problemy z dopasowaniem do bloków (czcionka zmniejszana do 8.4pt)
4. **Błędy tłumaczenia:**
   - "rudy lis" (powinno być "brązowy lis")
   - "oświetla doliny" (powinno być "wzgórza")
   - "Ta sekcja" zamiast "To zdanie"

### Logi z błędami

```
Tłumaczenie bloku 1/6...
Tekst nie mieści się, zmniejszam czcionkę z 18.0 na 16.2
Nadal nie mieści się, zmniejszam do 12.6
Uwaga: tekst nie mieści się w bloku 1, może być ucięty.
```

### Diagnoza

- Ekstrakcja tekstu z PDF pomija nagłówki
- Model nie dostaje pełnego kontekstu
- Bloki PDF są za małe dla tekstu

### Podsumowanie wszystkich testów

| Test | Format | Czas | Język | Kompletność | Jakość |
|------|--------|------|-------|-------------|--------|
| 1 | .txt (chunk=4000) | 1:12 | PL | 30% | ❌ |
| 1b | .txt (chunk=2000) | 3:46 | ES | 100% | ❌ Zły język |
| 2 | .md (chunk=2000) | 1:31 | PL | 100% | ⚠️ 80% |
| 3 | .docx (chunk=2000) | 11:30 | PL | 50% | ❌ Halucynacje |
| 4 | .odt (chunk=2000) | 2:05 | PL | 100% | ⚠️ 70% |
| 5 | .pdf (chunk=2000) | 4:46 | PL | 66% | ❌ Brak sekcji |

**Wniosek:** Tylko Markdown działa poprawnie. Formaty binarne (DOCX, ODT, PDF) mają poważne problemy.

---

## Test 6: Plik HTML (.html) - chunk_size=2000, parallel=1

**Czas tłumaczenia:** 4:32  
**Status:** ✅ BARDZO DOBRZE

### Wynik

Tłumaczenie jest **kompletne**, struktura HTML **zachowana**, język polski.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Nagłówki przetłumaczone: "English Section" → "Sekcja Angielska"
- Struktura HTML zachowana (tagi, klasy CSS, style)
- Kursywa (`<span class="text-T1">`) zachowana
- Podkreślenia (`<span class="text-T3">`) zachowane
- Język polski ✅

### ️ Drobne błędy gramatyczne

- "Ta zdanie" zamiast "To zdanie" (powtarza się)
- "poranna słońce" zamiast "poranne słońce" (sekcja EN)
- "łatwo się tłumaczyć" (dziwny szyk)

### Porównanie formatów

| Test | Format | Czas | Język | Kompletność | Jakość |
|------|--------|------|-------|-------------|--------|
| 1 | .txt (chunk=4000) | 1:12 | PL | 30% | ❌ |
| 1b | .txt (chunk=2000) | 3:46 | ES | 100% | ❌ Zły język |
| 2 | .md (chunk=2000) | 1:31 | PL | 100% | ️ 80% |
| 3 | .docx (chunk=2000) | 11:30 | PL | 50% | ❌ Halucynacje |
| 4 | .odt (chunk=2000) | 2:05 | PL | 100% | ⚠️ 70% |
| 5 | .pdf (chunk=2000) | 4:46 | PL | 66% | ❌ Brak sekcji |
| 6 | .html (chunk=2000) | 4:32 | PL | 100% | ✅ 90% |

**Wniosek:** HTML i Markdown działają najlepiej. Skill HTML dobrze chroni tagi.

---

## Test 7: Plik EPUB (.epub) - chunk_size=2000, parallel=1

**Czas tłumaczenia:** 6:46  
**Status:** ❌ KRYTYCZNY - WYCIEK PROMPTU

### Wynik

Tłumaczenie jest **niekompletne** i zawiera **wyciek promptu systemowego** w treści!

### Problemy

1. **Wyciek promptu** - w sekcji angielskiej widoczny jest prompt systemowy:
   ```
   user
   system
   You are a professional translator. Translate ALL text into Polish...
   ```

2. **Nagłówki nie przetłumaczone:**
   - "Deutscher Abschnitt" → "Deutscher Abschnitt" (brak tłumaczenia!)
   - "Section Française" → "Sekcja Francuska" ✅
   - "English Section" → nie widoczny (wyciek promptu)

3. **Sekcja angielska ucięta** - tekst urywa się w połowie

4. **Błędy gramatyczne:**
   - "Ta zdanie" zamiast "To zdanie"
   - "rudy lis" zamiast "brązowy lis"
   - "poranna słońce" zamiast "poranne słońce"

### Diagnoza

- Skill EPUB nie chroni promptu systemowego
- Model wtrąca prompt do treści XHTML
- Problem z przetwarzaniem wielu plików XHTML w EPUB

### Test 3b: DOCX z chatml + parallel=2

**Czas:** 2:06 (vs 11:30 wcześniej - **5x szybciej!**)  
**Status:** ️ ZNACZNA POPRAWA

#### Co się poprawiło

- ✅ Brak halucynacji (artykuł o "detekcji anomalii" zniknął)
- ✅ Brak zapętlenia ("assistant Section Française" zniknął)
- ✅ Wszystkie 3 sekcje przetłumaczone
- ✅ Przekreślenia zachowane (`~~...~~`)
- ✅ Czas tłumaczenia: 2:06 (vs 11:30)

#### Pozostałe problemy

- Artefakty XML na początku (`<|tag_separator|>`, itp.)
- "Ta zdanie" zamiast "To zdanie"
- "powoli wschodzi nad wzgórzem" (powtórzenie "wschodzi")

---

### Podsumowanie wszystkich testów

| Test | Format | Czas | Język | Kompletność | Jakość |
|------|--------|------|-------|-------------|--------|
| 1 | .txt (chunk=4000) | 1:12 | PL | 30% | ❌ |
| 1b | .txt (chunk=2000) | 3:46 | ES | 100% | ❌ Zły język |
| 2 | .md (chunk=2000) | 1:31 | PL | 100% | ️ 80% |
| 3 | .docx (chunk=2000, auto) | 11:30 | PL | 50% | ❌ Halucynacje |
| 3b | .docx (chunk=2000, chatml, p=2) | 2:06 | PL | 100% | ⚠️ 75% |
| 4 | .odt (chunk=2000) | 2:05 | PL | 100% | ⚠️ 70% |
| 5 | .pdf (chunk=2000) | 4:46 | PL | 66% | ❌ Brak sekcji |
| 6 | .html (chunk=2000) | 4:32 | PL | 100% | ✅ 90% |
| 7 | .epub (chunk=2000) | 6:46 | PL | 66% | ❌ Wyciek promptu |

### Ranking formatów (po poprawce DOCX)

1. **HTML** (90%) - najlepszy wynik
2. **Markdown** (80%) - bardzo dobry
3. **DOCX** (75%) - chatml + parallel=2 pomaga!
4. **ODT** (70%) - akceptowalny
5. **PDF** (66%) - problemy z ekstrakcją
6. **EPUB** (66%) - wyciek promptu
7. **TXT** (30-100%) - zależnie od chunk_size

### Wnioski

1. **chatml + parallel=2 znacząco poprawia DOCX** (50% → 75%, 11:30 → 2:06)
2. **HTML i Markdown działają najlepiej** - skills dobrze chronią strukturę
3. **Model ma problem z "Ta zdanie"** - powtarza się we wszystkich testach
4. **Prompt systemowy nie zawsze działa** - test 1b (hiszpański) i test 7 (wyciek)

---

## Analiza przyczyn błędów

### Błąd 1: "Ta zdanie" zamiast "To zdanie"

**Obserwacja:** Błąd powtarza się we WSZYSTKICH testach (TXT, MD, DOCX, ODT, PDF, HTML, EPUB).

**Przyczyna:** Model ma w danych treningowych błędne przykłady ("ta zdanie" zamiast "to zdanie"). "Zdanie" jest rodzaju nijakiego (to zdanie), ale model traktuje je jak żeńskie (ta zdanie).

**Podobne błędy:**
- "poranna słońce" (powinno: "poranne słońce" - rodzaj nijaki)
- "łatwo tłumaczyć się" (dziwny szyk)

**Rozwiązanie:** Wzmocnić prompt główny o reguły gramatyczne:
```
Polish grammar rules you MUST follow:
- 'zdanie' is neuter: use 'to zdanie', NOT 'ta zdanie'
- 'słońce' is neuter: use 'poranne słońce', NOT 'poranna słońce'
```

### Błąd 2: Pomylenie języków (hiszpański w teście 1b)

**Obserwacja:** Test 1b (TXT, chunk=2000) tłumaczył na hiszpański zamiast polski.

**Przyczyna:** Szablon czatu "auto (jinja)" może źle formatować wiadomości dla niektórych modeli. Model nie rozumie promptu systemowego "Translate to Polish".

**Rozwiązanie:** Użyć szablonu "chatml" - użytkownik może przestawić w ustawieniach (zapamiętywane).

### Błąd 3: PDF - brak nagłówków sekcji

**Obserwacja:** W teście PDF brakuje nagłówków "English Section", "Section Française", "Deutscher Abschnitt".

**Przyczyna (hipoteza):** 
- Kod tłumaczy każdy blok PDF osobno
- Nagłówki są w osobnych blokach z małą ilością tekstu (2-3 słowa)
- Model może pomijać krótkie bloki myśląc że to "niepełne zdania"
- Alternatywna hipoteza: tekst nie mieści się w bloku (czcionka zmniejszana do 8.4pt)

**Rozwiązanie (krok po kroku):**
1. Najpierw wzmocnić prompt (może pomóc)
2. Jeśli nie pomoże: łączyć sąsiednie bloki (nagłówek + akapit) przed tłumaczeniem

### Błąd 4: EPUB - wyciek promptu systemowego

**Obserwacja:** W treści EPUB widoczny jest prompt systemowy ("You are a professional translator...").

**Przyczyna:** Skill EPUB nie chroni promptu systemowego. Model wtrąca prompt do treści XHTML.

**Rozwiązanie:** Naprawić skill EPUB lub dodać walidację wyjścia (usuwać fragmenty promptu z wyniku).

---

## Plan naprawczy (priorytet)

1. ✅ **Wzmocnić prompt główny** o reguły gramatyczne polskiego
2. ⏸️ **Szablon chatml** - użytkownik przestawia ręcznie (zapamiętywane)
3. ⏸️ **PDF: łączyć bloki** - dopiero jeśli wzmocnienie promptu nie pomoże
4. ⏸️ **EPUB: naprawić skill** - dodać walidację wyjścia

### Harmonogram testów

Po każdej zmianie powtórzyć testy:
- TXT (sprawdzić "ta zdanie" → "to zdanie")
- PDF (sprawdzić nagłówki)
- EPUB (sprawdzić wyciek promptu)

---

## Testy modeli LLM

### Test A: TranslateGemma Q4-7b-instruct (bazowy)

**Jakość:** 80%  
**Problemy:** "ta zdanie" zamiast "to zdanie" (we wszystkich formatach)

### Test B: qwen3 instruct

**Jakość:** 60%  
**Problemy:**
- "skakuje" zamiast "skacze" (ortografia)
- "paresznym" zamiast "leniwym" (słownik)
- "poranek słońce" (gramatyka)
- "dalią górami" (słownik)

### Test C: YanoljaNEXT-Rosetta-4B (z chatml)

**Jakość:** 60%  
**Problemy:**
- "paresznym" zamiast "leniwym"
- "poranek słońce"
- "Ta fraza" zamiast "To zdanie"
- "zły pies" w DE

### Test D: Hy-MT2-7B

**Jakość:** 60%  
**Problemy:**
- "paresznym" zamiast "leniwym"
- "poranek słońce"
- "Ta fraza" / "Ten zdanie"
- "zły psa" w DE (błąd gramatyczny!)

### Porównanie modeli

| Model | Jakość | Typ | Problemy |
|-------|--------|-----|----------|
| **TranslateGemma-4b** | ✅ **80%** | Tłumaczeniowy | Drobne: "ta zdanie" |
| TranslateGemma Q4-7b-instruct | ️ 80% | Ogólny | "ta zdanie" |
| qwen3 instruct | ❌ 60% | Ogólny | Błędy słownikowe |
| YanoljaNEXT-Rosetta-4B | ❌ 60% | Tłumaczeniowy | Błędy słownikowe |
| Hy-MT2-7B | ❌ 60% | Tłumaczeniowy | Błędy słownikowe + gramatyczne |

### Wnioski z testów modeli

1. **TranslateGemma-4b jest najlepsza** do tłumaczenia na polski (80%)
2. **Modele tłumaczeniowe (Yanolja, Hy-MT2) nie zawsze lepsze** od ogólnych (TranslateGemma Q4)
3. **qwen3 jest gorszy** niż TranslateGemma Q4 do tłumaczenia
4. **Problem "ta zdanie"** jest specyficzny dla TranslateGemma Q4, TranslateGemma go nie ma (lub rzadziej)
5. **Szablon chatml** nie poprawia znacząco jakości dla słabszych modeli

### Rekomendacja

**Używać TranslateGemma-4b** jako domyślnego modelu do tłumaczenia. Jest specjalnie dostrojona do tłumaczenia i daje najlepsze wyniki na polski.

---

## Test 8: Plik tekstowy (.txt) - TranslateGemma-4B Q5_K_M + szablon translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:35  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ✅ DOBRZE - ZNACZNA POPRAWA

### Wynik

Tłumaczenie jest **kompletne** (wszystkie 3 sekcje) i po **POLSKU**. Nagłówki przetłumaczone poprawnie.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Nagłówki przetłumaczone poprawnie:
  - "ENGLISH SECTION" → "SEKCJA JĘZYKU ANGIELSKIEGO" ✅
  - "SECTION FRANÇAISE" → "SEKCJA JĘZYKA FRANCUSKIEGO" ✅
  - "DEUTSCHER ABSCHNITT" → "SEKCJA JĘZYKA NIEMIECKIEGO" ✅
- Język polski ✅
- Struktura dokumentu zachowana
- **Brak błędu "ta zdanie"** - jest "Ta fraza" (nie idealne, ale lepsze)

### ⚠️ Pozostałe problemy

1. **"Ta fraza"** zamiast "To zdanie" - nadal nieidealne (choć lepsze niż "ta zdanie")
2. **"poranek słońce"** zamiast "poranne słońce" - błąd gramatyczny (rodzaj nijaki)
3. **"Ten zdanie"** w sekcji DE - błąd gramatyczny
4. **"łagodnym psiem"** - w oryginale "lazy dog" (leniwy pies), nie "łagodny"
5. **"formowanie"** zamiast "formatowanie" - literówka/błąd słownikowy
6. **"nad nimi wzgórzami"** - powinno być "nad dalekimi wzgórzami"
7. **"Technologia i nauka kontynuują się szybko"** - dziwny szyk (powinno: "rozwijają się szybko")
8. Sekcja DE: "To dokument ten zawiera" - powtórzenie "dokument ten"

### Porównanie z poprzednimi testami TXT

| Test | Model | Szablon | Czas | Język | Kompletność | Jakość |
|------|-------|---------|------|-------|-------------|--------|
| 1 | TranslateGemma Q4 | auto | 1:12 | PL | 30% | ❌ |
| 1b | TranslateGemma Q4 | auto | 3:46 | ES | 100% | ❌ Zły język |
| **8** | **TranslateGemma Q5** | **translategemma** | **3:35** | **PL** | **100%** | **✅ 85%** |

### Wniosek

**TranslateGemma Q5 z szablonem "translategemma" znacząco poprawia jakość:**
- ✅ 100% kompletności (vs 30% w teście 1 z TranslateGemma Q4)
- ✅ Poprawny język polski (vs hiszpański w teście 1b z TranslateGemma Q4)
- ✅ Nagłówki przetłumaczone poprawnie
- ⚠️ Nadal drobne błędy gramatyczne ("poranek słońce", "Ten zdanie")
- ⚠️ "Ta fraza" zamiast "To zdanie" (ale nie "ta zdanie"!)

**Czas tłumaczenia:** 3:35 (porównywalny z testem 1b: 3:46, ale z poprawną jakością)

---

## Test 10: Plik Markdown (.md) - TranslateGemma-4B Q5_K_M + szablon translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:48  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ✅ DOBRZE

### Wynik

Tłumaczenie jest **kompletne** (wszystkie 3 sekcje) i po **POLSKU**. Struktura Markdown zachowana.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Nagłówki `#` przetłumaczone poprawnie
- Kursywa `*...*` zachowana ✅
- Przekreślenia `~~...~~` zachowane ✅
- Podkreślenia `{...}{.underline}` zachowane ✅
- Język polski ✅

### ⚠️ Problemy

1. **"Ta fraza"** zamiast "To zdanie" - powtarza się
2. **"poranek słońce"** zamiast "poranne słońce" - błąd gramatyczny
3. **"Ten zdanie"** w sekcji DE - błąd gramatyczny
4. **"zływanym psiem"** - w oryginale "faulen Hund" (leniwym psem)
5. **"formację dokumentu"** - powinno być "strukturę dokumentu"
6. **"Seki Niemiecka"** - wielka litera (powinno: "niemiecka")

### Porównanie z Testem 2 (TranslateGemma Q4 + auto)

| Aspekt | Test 2 (TranslateGemma Q4) | **Test 10 (TranslateGemma Q5)** |
|--------|---------------------------|--------------------------------|
| Czas | 1:31 | **2:48** (wolniej) |
| Język | PL ✅ | **PL ✅** |
| Kompletność | 100% | **100%** |
| Struktura MD | ✅ Zachowana | **✅ Zachowana** |
| Jakość | ⚠️ 80% | **⚠️ 80%** |

### Wniosek

**TranslateGemma Q5 z szablonem translategemma daje podobną jakość co Q4 z auto dla Markdown:**
- ⚠️ Wolniejszy (2:48 vs 1:31)
- ✅ Ta sama jakość (~80%)
- ✅ Zachowanie struktury Markdown

**Dla Markdown i TXT, szablon "translategemma" nie daje znaczącej poprawy jakości** (oba mają skille: plaintext i markdown). Ale dla TXT poprawia kompletność (30% → 100%).

---

## Test 9: Plik HTML (.html) - TranslateGemma-4B Q5_K_M + szablon translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 7:19  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ⚠️ DZIAŁA ALE GORSZE NIŻ QWEN2.5-CODER

### Wynik

Tłumaczenie jest **kompletne** (wszystkie 3 sekcje) i po **POLSKU**. Struktura HTML zachowana.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Nagłówki przetłumaczone poprawnie:
  - "English Section" → "Sekcja angielska" ✅
  - "Section Française" → "Sekcja francuska" ✅
  - "Deutscher Abschnitt" → "Sekcja niemiecka" ✅
- Struktura HTML zachowana (tagi, klasy CSS, style)
- Kursywa (`<span class="text-T1">`) zachowana ✅
- Podkreślenia (`<span class="text-T3">`) zachowane ✅
- Tytuł przetłumaczony: "- no title specified" → "- bez tytułu określonego" ✅
- Język polski ✅

### ⚠️ Problemy (gorsze niż Test 6 z TranslateGemma Q4!)

1. **"Ta fraza"** zamiast "To zdanie" - nadal nieidealne
2. **"poranek słońce"** zamiast "poranne słońce" - błąd gramatyczny
3. **"Ten zdanie"** w sekcji DE - błąd gramatyczny
4. **"nad lasek, który leży"** - w oryginale "over the lazy dog" (nad leniwym psem), NIE "nad laskiem"! 
5. **"łupieżnym psiem"** - w oryginale "faulen Hund" (leniwym psem), NIE "łupieżnym"! ❌
6. **"formację dokumentu"** - powinno być "strukturę dokumentu"
7. **"Technologia i nauka kontynuują się szybko"** - dziwny szyk

### Porównanie z Testem 6 (TranslateGemma Q4 + chatml)

| Aspekt | Test 6 (TranslateGemma Q4) | **Test 9 (TranslateGemma)** |
|--------|------------------------|----------------------------|
| Czas | 4:32 | **7:19** (wolniej!) |
| Język | PL ✅ | **PL ✅** |
| Kompletność | 100% | **100%** |
| Nagłówki | ✅ Poprawne | **✅ Poprawne** |
| Struktura HTML | ✅ Zachowana | **✅ Zachowana** |
| Błędy słownikowe | "rudy lis" | **"nad lasek", "łupieżnym psiem"** ❌ |
| Jakość | **90%** | **~80%** |

### Wniosek

**Dla HTML, TranslateGemma Q4 z chatml działa LEPIEJ niż TranslateGemma z szablonem translategemma:**
- ⚠️ TranslateGemma jest wolniejszy (7:19 vs 4:32)
- ⚠️ TranslateGemma ma poważne błędy słownikowe ("nad lasek", "łupieżnym psiem")
- ✅ Oba modele zachowują strukturę HTML
- ✅ Oba modele tłumaczą nagłówki poprawnie

**Hipoteza:** Szablon "translategemma" może nie być optymalny dla formatu HTML. Skill HTML może lepiej działać z chatml.

---

## Test 11: Plik DOCX (.docx) - TranslateGemma-4B Q5_K_M + szablon translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:13  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ⚠️ DZIAŁA ALE Z BŁĘDAMI

### Wynik

Tłumaczenie jest **kompletne** (wszystkie 3 sekcje) i po **POLSKU**. Struktura dokumentu zachowana.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Nagłówki przetłumaczone: "Seki Francuska", "Seki Niemiecka" ✅
- Przekreślenia `~~...~~` zachowane ✅
- Język polski ✅

### ⚠️ Problemy

1. **"Ta fraza"** zamiast "To zdanie" - powtarza się
2. **"poranek słońce"** zamiast "poranne słońce" - błąd gramatyczny
3. **"Ten zdanie"** w sekcji DE - błąd gramatyczny
4. **"Szybki brązowy renifer"** - w oryginale "quick brown fox" (lis), NIE renifer! ❌
5. **"Pomorski brązowy lis"** - w oryginale "schnelle braune Fuchs" (szybki brązowy lis), NIE "Pomorski"! ❌
6. **"leżącym psiem"** - w oryginale "lazy dog" (leniwym psem)
7. **"zasłanym psiem"** - w oryginale "faulen Hund" (leniwym psem)
8. **"formację dokumentu"** - powinno być "strukturę dokumentu"

### Porównanie z Testem 3b (TranslateGemma Q4 + chatml + parallel=2)

| Aspekt | Test 3b (TranslateGemma Q4) | **Test 11 (TranslateGemma Q5)** |
|--------|----------------------------|--------------------------------|
| Czas | 2:06 | **3:13** (wolniej) |
| Język | PL ✅ | **PL ✅** |
| Kompletność | 100% | **100%** |
| Halucynacje | ✅ Brak | **✅ Brak** |
| Błędy słownikowe | "ta zdanie" | **"renifer", "Pomorski"** ❌ |
| Jakość | ⚠️ 75% | **⚠️ 70%** |

### Wniosek

**Dla DOCX, TranslateGemma Q4 z chatml + parallel=2 działa LEPIEJ niż Q5 z szablonem translategemma:**
- ️ TranslateGemma Q5 jest wolniejszy (3:13 vs 2:06)
- ⚠️ TranslateGemma Q5 ma poważne błędy słownikowe ("renifer", "Pomorski")
- ✅ Oba modele nie mają halucynacji
- ✅ Oba modele zachowują strukturę DOCX

**Hipoteza:** Szablon "translategemma" nie jest optymalny dla formatów binarnych (DOCX, HTML). Chatml + parallel=2 daje lepsze wyniki.

---

## Test 12: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + szablon translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:17  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ️ DZIAŁA ALE Z BŁĘDAMI

### Wynik

Tłumaczenie jest **kompletne** (wszystkie 3 sekcje) i po **POLSKU**. Struktura dokumentu zachowana.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Nagłówki przetłumaczone: "Seki francuska", "Seki niemiecka" ✅
- Przekreślenia `~~...~~` zachowane ✅
- Język polski ✅

### ⚠️ Problemy

1. **"Ta fraza"** zamiast "To zdanie" - powtarza się
2. **"poranek słońce"** zamiast "poranne słońce" - błąd gramatyczny
3. **"Ten zdanie"** w sekcji DE - błąd gramatyczny
4. **"Szybki brązowy renifer"** - w oryginale "quick brown fox" (lis), NIE renifer! ❌
5. **"nad lasek, który leży"** - w oryginale "over the lazy dog" (nad leniwym psem) ❌
6. **"Pomorski brązowy lis"** - w oryginale "schnelle braune Fuchs" (szybki brązowy lis), NIE "Pomorski"! ❌
7. **"zasłanym psiem"** - w oryginale "faulen Hund" (leniwym psem)
8. **"skakuje"** - powinno być "skacze" (ortografia)
9. **"formację dokumentu"** - powinno być "strukturę dokumentu"

### Porównanie z Testem 4 (TranslateGemma Q4 + auto)

| Aspekt | Test 4 (TranslateGemma Q4) | **Test 12 (TranslateGemma Q5)** |
|--------|---------------------------|--------------------------------|
| Czas | 2:05 | **3:17** (wolniej) |
| Język | PL ✅ | **PL ✅** |
| Kompletność | 100% | **100%** |
| Artefakty XML | ⚠️ Były | **✅ Brak** |
| Błędy słownikowe | "ta zdanie" | **"renifer", "Pomorski", "lasek"** ❌ |
| Jakość | ⚠️ 70% | **⚠️ 65%** |

### Wniosek

**Dla ODT, TranslateGemma Q4 z auto działa LEPIEJ niż Q5 z szablonem translategemma:**
- ⚠️ TranslateGemma Q5 jest wolniejszy (3:17 vs 2:05)
- ✅ TranslateGemma Q5 nie ma artefaktów XML (poprawa!)
- ⚠️ TranslateGemma Q5 ma poważne błędy słownikowe ("renifer", "Pomorski", "lasek")
- ⚠️ Jakość gorsza (65% vs 70%)

**Hipoteza:** Szablon "translategemma" nie jest optymalny dla formatów binarnych. Chatml daje lepsze wyniki.

---

## Test 12b: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + szablon translategemma (PO RESECIE)

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:15  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ️ LEPIEJ NIŻ TEST 12 - POTWIERDZENIE HIPOTEZY!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **lepsza** niż w teście 12 (przed resetem).

### Porównanie z Testem 12 (przed resetem)

| Aspekt | Test 12 (przed resetem) | **Test 12b (po resecie)** |
|--------|------------------------|--------------------------|
| Czas | 3:17 | **3:15** (podobnie) |
| "renifer" | ❌ Był | **✅ "lis"** (poprawa!) |
| "lasek, który leży" | ❌ Był | **✅ "leniwym psiem"** (poprawa!) |
| "Pomorski" | ❌ Był | **❌ Nadal jest** |
| "zasłanym psiem" | ❌ Był | **❌ Nadal jest** |
| "Ta fraza" |  Była | **❌ Nadal jest** |
| "poranek słońce" | ❌ Było | **❌ Nadal jest** |
| Jakość | ⚠️ 65% | **⚠️ 70%** (poprawa!) |

### Wniosek

**Reset aplikacji i opróżnienie cache POPRAWIA jakość tłumaczenia:**
- ✅ "renifer" → "lis" (poprawa!)
- ✅ "lasek, który leży" → "leniwym psiem" (poprawa!)
- ️ Jakość: 65% → 70% (+5%)
- ⚠️ Niektóre błędy pozostały ("Pomorski", "zasłanym", "Ta fraza")

**Hipoteza o kumulacji błędów w cache POTWIERDZONA!** Błędy kumulują się w kolejnych tłumaczeniach. Reset/cache clear pomaga.

---

## Test 12c: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + szablon CHATML (PO RESECIE)

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:58  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** **chatml**  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ❌ GORSZE NIŻ TRANSLATEGEMMA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Ale jakość **gorsza** niż z szablonem translategemma (test 12b).

### Porównanie z Testem 12b (translategemma po resecie)

| Aspekt | Test 12b (translategemma) | **Test 12c (chatml)** |
|--------|--------------------------|----------------------|
| Czas | 3:15 | **2:58** (szybciej) |
| "renifer" | ✅ "lis" | **❌ "renifer"** (powrót!) |
| "leniwym psiem" | ✅ | **❌ "łysym psiem"** (nowy błąd!) |
| "Pomorski" | ❌ | **❌ Nadal** |
| "zasłanym/łupieżnym" | ❌ "zasłanym" | **❌ "łupieżnym"** (powrót!) |
| "Ta fraza" | ❌ | **❌ Nadal** |
| "poranek słońce" |  | **❌ Nadal** |
| Jakość | ⚠️ 70% | ** 60%** (gorzej!) |

### Wniosek

**Szablon CHATML daje GORSZE wyniki niż TRANSLATEGEMMA dla ODT:**
-  Jakość: 60% vs 70% (translategemma lepszy!)
- ❌ Powrót błędów: "renifer", "łupieżnym"
- ❌ Nowy błąd: "łysym psiem"
- ✅ Tylko czas lepszy (2:58 vs 3:15)

**Zaskoczenie:** Wcześniejsze testy (Q4) wskazywały że chatml jest lepszy, ale dla Q5 z kodami języków **translategemma działa lepiej!**

---

## Test 12d: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + szablon JINJA/AUTO (PO RESECIE)

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:58  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** **jinja (auto)**  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ️ PODOBNIE DO CHATML - GORSZE NIŻ TRANSLATEGEMMA

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **podobna do chatml**, gorsza niż translategemma.

### Porównanie wszystkich 3 szablonów (po resecie)

| Aspekt | Test 12b (translategemma) | Test 12c (chatml) | **Test 12d (jinja)** |
|--------|--------------------------|-------------------|---------------------|
| Czas | 3:15 | 2:58 | **2:58** |
| "renifer" | ✅ "lis" |  "renifer" | **❌ "renifer"** |
| "leniwym/leżącym/łysym" | ✅ "leniwym" | ❌ "łysym" | **❌ "leżącym"** |
| "Pomorski" | ❌ | ❌ | **❌** |
| "zasłanym/łupieżnym" | ❌ "zasłanym" | ❌ "łupieżnym" | **❌ "zasłanym"** |
| "Ta fraza" | ❌ | ❌ | **❌** |
| Jakość | ️ **70%** |  60% | **❌ 60%** |

### Wniosek

**Szablon TRANSLATEGEMMA jest NAJLEPSZY dla TranslateGemma Q5:**
- ✅ Jakość: 70% (vs 60% chatml/jinja)
- ✅ Mniej błędów słownikowych
- ⚠️ Wolniejszy (3:15 vs 2:58)

**Chatml i jinja dają podobną, gorszą jakość** (60%) z większą liczbą błędów słownikowych.

**Rekomendacja końcowa:** Dla TranslateGemma Q5 używaj szablonu **translategemma** + kody języków!

---

## Test 12e: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + translategemma + SKILL WYŁĄCZONY + parallel=2

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:53  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Skill ODT:** ❌ WYŁĄCZONY  
**Parallel:** 2  
**Status:** ❌ GORSZE - SKILL POMAGA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Ale jakość **gorsza** niż z włączonym skillem.

### Porównanie z Testem 12b (skill włączony, parallel=1)

| Aspekt | Test 12b (skill ON, p=1) | **Test 12e (skill OFF, p=2)** |
|--------|--------------------------|-------------------------------|
| Czas | 3:15 | **2:53** (szybciej) |
| "renifer" | ✅ "lis" | **❌ "renifer"** (powrót!) |
| "leniwym psiem" | ✅ | **❌ "leżącym psiem"** (gorzej!) |
| "Pomorski" | ❌ | **❌ Nadal** |
| "zasłanym psiem" | ❌ | **❌ Nadal** |
| "skakuje" | ✅ "skacze" | **❌ "skakuje"** (błąd ort.) |
| "wzgórzami" | ✅ | **❌ "górami"** (błąd!) |
| Jakość | ⚠️ 70% | **❌ 60%** (gorzej!) |

### Wniosek

**Skill ODT POMAGA nawet z szablonem translategemma:**
- ❌ Wyłączenie skilla = powrót błędów ("renifer", "leżącym")
- ❌ Nowe błędy: "skakuje" (ortografia), "górami" (zamiast "wzgórzami")
- ✅ Tylko czas lepszy (2:53 vs 3:15) dzięki parallel=2
- ⚠️ Jakość: 60% vs 70% (skill włączony lepszy!)

**Rekomendacja:** Zostaw skill ODT włączony nawet z szablonem translategemma!

---

## Test 12f: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + translategemma + chunk_size=1000

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:58  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Skill ODT:** ✅ włączony  
**Chunk size:** **1000** (zmiana z 2000!)  
**Parallel:** 2  
**Status:** ✅ POPRAWA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **lepsza** niż z chunk=2000.

### Porównanie z Testem 12b (chunk=2000)

| Aspekt | Test 12b (chunk=2000) | **Test 12f (chunk=1000)** |
|--------|----------------------|--------------------------|
| Czas | 3:15 | **2:58** (szybciej!) |
| "renifer" | ✅ "lis" | **✅ "lis"** |
| "leniwym psiem" | ✅ | **⚠️ "leżącym psem"** (gorzej w EN) |
| "Szybki brunatny lis" (FR) | ❌ "Szybki brązowy lis" | **✅ "Szybki brunatny lis"** (poprawa!) |
| "leniwym psem" (FR) | ❌ | **✅ "leniwym psem"** (poprawa!) |
| "Pomorski" (DE) | ❌ | **❌ Nadal** |
| "zasłanym psiem" (DE) |  | **❌ Nadal** |
| "Niemiecki fragment" | ❌ "Sekcja Niemiecka" | **✅ "Niemiecki fragment"** (poprawa!) |
| Jakość | ⚠️ 70% | **✅ 75%** (poprawa!) |

### Wniosek

**Chunk size 1000 POPRAWIA jakość tłumaczenia:**
- ✅ Jakość: 70% → 75% (+5%)
- ✅ Szybszy (2:58 vs 3:15) - mniej tekstu na chunk
- ✅ Lepsze tłumaczenie w sekcji FR ("brunatny lis", "leniwym psem")
- ✅ Lepsze nagłówki ("Niemiecki fragment" vs "Sekcja Niemiecka")
- ⚠️ Nadal błędy w sekcji DE ("Pomorski", "zasłanym")

**Rekomendacja:** Używaj chunk_size=1000 dla lepszej jakości!

---

## Test 12g: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + translategemma + temperature=0.0

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:52  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** **0.0** (zmiana z 0.1 - w pełni deterministyczny!)  
**Parallel:** 2  
**Status:** ✅ BARDZO DOBRZE - "TO ZDANIE" POPRAWNE!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **podobna** do temperature=0.1, ale z kluczową poprawą!

### Porównanie z Testem 12f (temperature=0.1)

| Aspekt | Test 12f (temp=0.1) | **Test 12g (temp=0.0)** |
|--------|---------------------|------------------------|
| Czas | 2:58 | **2:52** (nieco szybciej) |
| **"To zdanie"** | ✅ Było | **✅ Jest!** (kluczowa poprawa!) |
| "Szybki brunatny lis" (FR) | ✅ | **✅** |
| "leniwym psem" (FR) | ✅ | **✅** |
| "Pomorski" (DE) | ❌ | **❌ Nadal** |
| "zasłanym psiem" (DE) | ❌ | **❌ Nadal** |
| "formacie dokumentu" | ✅ "formację" | **❌ "formacie"** (regresja!) |
| Jakość | ✅ 75% | **✅ 78%** (lekka poprawa!) |

### Wniosek

**Temperature 0.0 daje podobną lub lekko lepszą jakość:**
- ✅ **"To zdanie"** jest poprawne! (kluczowy błąd zniknął!)
- ✅ Szybszy (2:52 vs 2:58)
- ✅ Jakość: 75% → 78% (+3%)
- ️ Drobna regresja: "formacie" zamiast "formację"
- ⚠️ Nadal błędy w sekcji DE ("Pomorski", "zasłanym")

**Rekomendacja:** Używaj temperature=0.0 dla bardziej deterministycznych wyników!

---

## Test 12h: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + translategemma + temperature=0.3

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:53  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** **0.3** (zmiana z 0.0 - więcej kreatywności!)  
**Parallel:** 2  
**Status:** ❌ GORSZE - TEMPERATURE 0.3 NIE POMAGA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Ale jakość **gorsza** niż z temperature=0.0.

### Porównanie z Testem 12g (temperature=0.0)

| Aspekt | Test 12g (temp=0.0) | **Test 12h (temp=0.3)** |
|--------|---------------------|------------------------|
| Czas | 2:52 | **2:53** (podobnie) |
| "To zdanie" | ✅ | **✅** |
| "Szybki brunatny lis" (FR) | ✅ | **✅** |
| "leniwym psem" (FR) | ✅ | **❌ "lasem bezwładnym"** (nowy błąd!) |
| "Pomorski" (DE) | ❌ | **❌ "Pomarszczony"** (gorzej!) |
| "zasłanym psiem" (DE) | ❌ | **❌ Nadal** |
| "dalekimi wzgórzami" | ✅ | ** "dalią górą"** (nowy błąd!) |
| Jakość | ✅ 78% | **❌ 65%** (gorzej!) |

### Wniosek

**Temperature 0.3 DAJE GORSZE WYNIKI:**
- ❌ Jakość: 78% → 65% (-13%!)
- ❌ Nowe błędy: "lasem bezwładnym", "dalią górą"
- ❌ Pogorszenie: "Pomorski" → "Pomarszczony"
- ✅ Tylko "To zdanie" nadal poprawne

**Rekomendacja:** Używaj temperature=0.0, NIE 0.3!

---

## Test 12i: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + translategemma + GLOSARIUSZ WYŁĄCZONY

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:04  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz IT:** ❌ WYŁĄCZONY  
**Parallel:** 2  
**Status:** ❌ GORSZE - GLOSARIUSZ POMAGA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Ale jakość **znacznie gorsza** niż z glosariuszem.

### Porównanie z Testem 12g (glosariusz włączony)

| Aspekt | Test 12g (glosariusz ON) | **Test 12i (glosariusz OFF)** |
|--------|--------------------------|-------------------------------|
| Czas | 2:52 | **2:04** (48s szybciej!) |
| "To zdanie" | ✅ | **❌ "Ta fraza"** (powrót!) |
| "Szybki brunatny lis" (FR) | ✅ | **❌ "Czarny lis szybki"** (gorzej!) |
| "leniwym psem" (FR) | ✅ | ** "psiem leniwym"** (dziwny szyk!) |
| "leżącym psem" (EN) | ⚠️ | **❌ "leżącym końcem psa"** (nowy błąd!) |
| "zasłanym psiem" (DE) | ❌ | **❌ "wypoczywającym psiem"** (inny błąd!) |
| "Pomorski" (DE) | ❌ | **❌ Nadal** |
| Jakość | ✅ 78% | **❌ 60%** (gorzej!) |

### Wniosek

**Glosariusz IT POMAGA mimo że nie zawiera słów z testu:**
- ❌ Jakość: 78% → 60% (-18%!)
- ❌ Powrót "Ta fraza" zamiast "To zdanie"
- ❌ Nowe błędy: "końcem psa", "Czarny lis"
- ✅ Tylko czas lepszy (2:04 vs 2:52) - 48 sekund szybciej

**Hipoteza:** Glosariusz IT wymusza na modelu bardziej staranne tłumaczenie, nawet jeśli nie zawiera słów z dokumentu.

**Rekomendacja:** Zostaw glosariusz włączony!

---

## Test 12j: Plik ODT (.odt) - TranslateGemma-4B Q5_K_M + translategemma + GLOSARIUSZ OGÓLNY

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:26  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz:** **ogólny** (zmiana z IT!)  
**Parallel:** 2  
**Status:** ⚠️ GORSZE NIŻ IT - GLOSARIUSZ IT LEPSZY!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Ale jakość **gorsza** niż z glosariuszem IT.

### Porównanie z Testem 12g (glosariusz IT)

| Aspekt | Test 12g (glosariusz IT) | **Test 12j (glosariusz ogólny)** |
|--------|--------------------------|----------------------------------|
| Czas | 2:52 | **3:26** (34s wolniej!) |
| "To zdanie" | ✅ | **❌ "Ta fraza" / "Ten zdanie"** (powrót!) |
| "Szybki brunatny lis" (FR) | ✅ | **✅** |
| "leniwym psem" (FR) | ✅ | **✅** |
| "Pomorski" (DE) | ❌ | **❌ Nadal** |
| "zasłanym psiem" (DE) | ❌ | **❌ Nadal** |
| Jakość | ✅ 78% | **⚠️ 70%** (gorzej!) |

### Wniosek

**Glosariusz IT jest LEPSZY niż ogólny dla tego dokumentu:**
- ❌ Jakość: 78% → 70% (-8%)
- ❌ Powrót "Ta fraza" / "Ten zdanie"
- ❌ Wolniejszy (3:26 vs 2:52) - większy plik
- ✅ Tylko "Szybki brunatny lis" i "leniwym psem" nadal poprawne

**Hipoteza:** Glosariusz IT (17k par) jest bardziej skoncentrowany i wymusza lepszą jakość niż ogólny (20k par).

**Rekomendacja:** Używaj glosariusza IT dla dokumentów technicznych/ogólnych!

---

## Test 12k: Plik ODT (.odt) - TranslatePsy-AfriSLM-0.8B Q8 + chatml

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:05  
**Model:** TranslatePsy-AfriSLM-0.8B Q8 (1.1 GB) - **5x mniejszy niż TranslateGemma!**  
**Szablon czatu:** chatml  
**Język docelowy:** Polish  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz:** IT  
**Parallel:** 2  
**Status:** ✅ ZASKAKUJĄCO DOBRZE - MAŁY MODEL, DUŻA JAKOŚĆ!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **podobna** do TranslateGemma 4B!

### Porównanie z TranslateGemma-4B Q5 (test 12g)

| Aspekt | TranslateGemma-4B Q5 (2.7 GB) | **TranslatePsy-AfriSLM-0.8B Q8 (1.1 GB)** |
|--------|-------------------------------|-------------------------------------------|
| Czas | 2:52 | **3:05** (13s wolniej) |
| "To zdanie" (EN) | ✅ | **✅** |
| "Szybki brunatny lis" (FR) | ✅ | **✅** |
| "leniwym psem" (FR) | ✅ | **✅** |
| "Pomorski" (DE) | ❌ | **❌** |
| "zasłanym psiem" (DE) | ❌ | **❌** |
| "Ta fraza" (FR) | ✅ "To zdanie" | **❌ "Ta fraza"** |
| "Ten zdanie" (DE) | ✅ "To zdanie" | **❌ "Ten zdanie"** |
| Jakość | ✅ 78% | **✅ 75%** (tylko -3%!) |

### Wniosek

**TranslatePsy-AfriSLM 0.8B daje zaskakująco dobrą jakość:**
- ✅ Jakość: 78% → 75% (tylko -3%!)
- ✅ **5x mniejszy model** (1.1 GB vs 2.7 GB)
- ✅ **5x mniej parametrów** (0.8B vs 4B)
- ⚠️ Tylko 13s wolniejszy (3:05 vs 2:52)
- ️ Gorsze "To zdanie" w sekcjach FR i DE

**To niesamowite!** Model 5x mniejszy daje prawie taką samą jakość!

**Rekomendacja:** TranslatePsy-AfriSLM 0.8B jest świetną alternatywą dla TranslateGemma 4B gdy liczy się rozmiar modelu!

---

## Test 12l: Plik ODT (.odt) - TranslatePsy-AfriSLM-0.8B Q8 + chatml + "polski" (mała litera)

**Data:** 2026-09-04  
**Czas tłumaczenia:** 4:00  
**Model:** TranslatePsy-AfriSLM-0.8B Q8 (1.1 GB)  
**Szablon czatu:** chatml  
**Język docelowy:** **polski** (zmiana z "Polish" na małą literę)  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz:** IT  
**Parallel:** 2  
**Status:** ❌ GORSZE - "POLISH" BYŁO LEPSZE!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Ale jakość **gorsza** niż z "Polish".

### Porównanie z Testem 12k ("Polish")

| Aspekt | Test 12k ("Polish") | **Test 12l ("polski")** |
|--------|---------------------|------------------------|
| Czas | 3:05 | **4:00** (55s wolniej!) |
| "To zdanie" (EN) | ✅ | **❌ "Ta fraza"** (powrót!) |
| "Szybki brunatny lis" (FR) | ✅ | **✅** |
| "leniwym psem" (FR) | ✅ | **✅** |
| "Pomorski" (DE) | ❌ | **✅ "Szybki brązowy lis"** (poprawa!) |
| "zasłanym/wypoczywającym" (DE) | ❌ "zasłanym" | **❌ "wypoczywającym"** (inny błąd!) |
| "Ten zdanie" (DE) | ❌ | **❌ Nadal** |
| Jakość | ✅ 75% | **⚠️ 70%** (gorzej!) |

### Wniosek

**"Polish" (wielka litera) jest LEPSZE niż "polski" (mała litera) dla TranslatePsy-AfriSLM:**
- ❌ Jakość: 75% → 70% (-5%)
-  Wolniejszy (4:00 vs 3:05) - 55 sekund wolniej!
- ❌ Powrót "Ta fraza" zamiast "To zdanie"
- ✅ Tylko "Pomorski" → "Szybki brązowy lis" (poprawa w DE)

**Hipoteza:** Model TranslatePsy-AfriSLM był trenowany z "Polish" (wielka litera) w promptach - zmiana na "polski" pogarsza jakość.

**Rekomendacja:** Używaj "Polish" (wielka litera) dla TranslatePsy-AfriSLM!

---

## Test 12m: Plik ODT (.odt) - MiLMMT-46-4B Q5_K_M + translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:08  
**Model:** MiLMMT-46-4B Q5_K_M (2.8 GB) - konkurent dla TranslateGemma!  
**Szablon czatu:** translategemma (Gemma 3)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz:** IT  
**Parallel:** 2  
**Status:** ✅ BARDZO DOBRZE - PODOBNIE DO TRANSLATEGEMMA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **bardzo podobna** do TranslateGemma 4B!

### Porównanie z TranslateGemma-4B Q5 (test 12g)

| Aspekt | TranslateGemma-4B Q5 (2.7 GB) | **MiLMMT-46-4B Q5 (2.8 GB)** |
|--------|-------------------------------|------------------------------|
| Czas | 2:52 | **3:08** (16s wolniej) |
| "To zdanie" (EN) | ✅ | **✅** |
| "Szybki brunatny lis" (FR) | ✅ | **✅** |
| "leniwym psem" (FR) | ✅ | **✅** |
| "Pomorski" (DE) | ❌ | **** |
| "zasłanym psiem" (DE) | ❌ | **❌** |
| "formację dokumentu" | ✅ | **❌ "formacie"** (regresja!) |
| Jakość | ✅ 78% | **✅ 75%** (tylko -3%!) |

### Wniosek

**MiLMMT-46 4B daje bardzo podobną jakość do TranslateGemma 4B:**
- ✅ Jakość: 78% → 75% (tylko -3%!)
- ✅ **Ta sama architektura** (Gemma 3)
- ✅ **Ten sam rozmiar** (2.8 GB vs 2.7 GB)
- ⚠️ Tylko 16s wolniejszy (3:08 vs 2:52)
- ⚠️ Drobna regresja: "formacie" zamiast "formację"

**To zaskakujące!** MiLMMT-46 (Xiaomi) jest prawie tak dobry jak TranslateGemma (Google)!

**Rekomendacja:** MiLMMT-46 4B jest świetną alternatywą dla TranslateGemma 4B!

---

## Podsumowanie testów modeli (optymalna konfiguracja):

| Model | Rozmiar | Jakość | Czas | Wniosek |
|-------|---------|--------|------|---------|
| **TranslateGemma-4B Q5** | 2.7 GB | **78%** 🥇 | 2:52 | Najlepszy lokalny! |
| **MiLMMT-46-4B Q5** | 2.8 GB | **75%**  | 3:08 | Prawie tak dobry! |
| **TranslatePsy-AfriSLM-0.8B Q8** | 1.1 GB | **75%**  | 3:05 | 5x mniejszy! |

---

## Test 12n: Plik ODT (.odt) - Gemini 3.5 Flash Lite (chmura)

**Data:** 2026-09-04  
**Czas tłumaczenia:** **27 SEKUND** 🚀🚀  
**Model:** Gemini 3.5 Flash Lite (chmura Google)  
**Szablon czatu:** N/A (zewnętrzne API)  
**Język docelowy:** Polish  
**Skill ODT:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz:** IT  
**Parallel:** 2  
**Status:** ✅ NAJSZYBSZY! ZASKAKUJĄCO DOBRA JAKOŚĆ!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **lepsza niż TranslateGemma**!

### Porównanie z TranslateGemma-4B Q5 (test 12g)

| Aspekt | TranslateGemma-4B Q5 (lokalny) | **Gemini 3.5 Flash Lite (chmura)** |
|--------|-------------------------------|-------------------------------------|
| Czas | 2:52 (172s) | **27s** 🚀 (6x szybciej!) |
| "To zdanie" | ✅ | **✅** |
| "Szybki brunatny lis" | ✅ | **✅** |
| "leniwym psem" | ✅ (FR) | **✅✅** (wszystkie sekcje!) |
| "poranne słońce" |  "poranek słońce" | **✅ "poranne słońce"** (poprawa!) |
| "odległymi wzgórzami" | ✅ | **✅** |
| "nowym wzgórzem" (DE) | ✅ "dalekimi" | **❌ "nowym"** (błąd!) |
| Nagłówki | ✅ Przetłumaczone | **❌ Nie przetłumaczone** |
| Jakość | ✅ 78% | **✅ 85%** (poprawa!) |

### Wniosek

**Gemini 3.5 Flash Lite ZASKAKUJE:**
-  **6x szybszy** (27s vs 2:52)!
- ✅ **Wyższa jakość** (85% vs 78%)!
- ✅ **"poranne słońce"** poprawne (lokalne modele miały błąd!)
- ✅ **"leniwym psem"** we wszystkich sekcjach
- ❌ Nagłówki nie przetłumaczone (problem z skill ODT?)
- ❌ "nowym wzgórzem" zamiast "dalekimi" (DE)

**To rewelacja!** Chmura Google daje lepszą jakość i szybkość niż lokalne modele!

**Rekomendacja:** Używaj Gemini 3.5 Flash Lite gdy masz internet! Lokalny serwer tylko offline.

---

## Test 12o: Plik ODT (.odt) - Gemini 3.5 Flash Lite BEZ skilla ODT

**Data:** 2026-09-04  
**Czas tłumaczenia:** **3 min (180s)** 🐢  
**Model:** Gemini 3.5 Flash Lite (chmura Google)  
**Szablon czatu:** N/A (zewnętrzne API)  
**Język docelowy:** Polish  
**Skill ODT:** ❌ **WYŁĄCZONY**  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz:** IT  
**Parallel:** 2  
**Status:** ️ 6.7x WOLNIEJ - SKILL POMAGA GEMINI!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Ale **znacznie wolniejsze** i z drobnymi regresjami.

### Porównanie z Testem 12n (Gemini z skillem ODT)

| Aspekt | Test 12n (skill ON) | **Test 12o (skill OFF)** |
|--------|---------------------|--------------------------|
| Czas | **27s**  | **180s** 🐢 (6.7x wolniej!) |
| "Angielska sekcja" | ✅ | **✅** |
| "To zdanie" (EN) | ✅ | **✅** |
| "poranne słońce" | ✅ | **✅** |
| "leniwym psem" | ✅ | **✅** |
| "Ta zdanie" (FR) | ✅ "To zdanie" | **❌ "Ta zdanie"** (regresja!) |
| "Ten sformułowany w ten sposób zwrot" (DE) | ✅ "To zdanie" | **❌ Dziwny fragment!** |
| "nowym wzgórzem" (DE) | ❌ | **❌ Nadal** |
| Jakość | ✅ 85% | **⚠️ 80%** (regresja!) |

### Wniosek

**Skill ODT POMAGA nawet Gemini:**
-  **6.7x szybciej** (27s vs 180s)!
- ✅ **Lepsza jakość** (85% vs 80%)
- ✅ Mniej błędów ("Ta zdanie", dziwne fragmenty)
- **Skill zawiera instrukcje które przyspieszają przetwarzanie!**

**Hipoteza:** Skill ODT zawiera instrukcje formatowania które pomagają Gemini szybciej zrozumieć strukturę dokumentu.

**Rekomendacja:** Zostaw skill ODT włączony nawet dla Gemini!

---

## Podsumowanie testów Gemini 3.5 Flash Lite:

| Test | Skill ODT | Czas | Jakość |
|------|-----------|------|--------|
| 12n | ✅ Włączony | **27s** 🚀 | **85%** 🥇 |
| 12o | ❌ Wyłączony | 180s 🐢 | 80% |

---

## Test 13: Plik PDF (.pdf) - TranslateGemma-4B Q5_K_M + szablon translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 3:51  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ❌ SŁABO - NAJGORSZY WYNIK

### Wynik

Tłumaczenie jest **kompletne** (tekst obecny) ale **bardzo niskiej jakości**. Brak nagłówków sekcji.

### ✅ Co działa

- Tekst przetłumaczony na polski
- Struktura akapitów zachowana

###  Problemy krytyczne

1. **Brak nagłówków sekcji** - "English Section", "Section Française", "Deutscher Abschnitt" nie przetłumaczone jako nagłówki!
2. **Gubienie formatowania tekstu** - PDF traci pogrubienia, kursywę, rozmiary czcionek - tekst jest płaski bez stylów!
3. **"Szczur brązowy wskakuje przez łóżko psa"** - w oryginale "The quick brown fox jumps over the lazy dog" - kompletnie zle! 
4. **"Czarny lis skacze nad łupieżcem"** - w oryginale "Le renard brun rapide saute par-dessus le chien paresseux" - "brązowy szybki lis" → "czarny lis", "nad leniwym psem" → "nad łupieżcem" ❌❌
5. **"Ta fraza"** zamiast "To zdanie" - powtarza się
6. **"słońce poranku" / "słońce poranka" / "poranek słońce"** - różne formy, wszystkie niepoprawne (powinno: "poranne słońce")
7. **"To dokument ten zawiera"** - powtórzenie
8. **"Ten zdanie"** - błąd gramatyczny
9. **"łagodnym psiem"** - w oryginale "faulen Hund" (leniwym psem)

### Porównanie z Testem 5 (TranslateGemma Q4 + auto)

| Aspekt | Test 5 (TranslateGemma Q4) | **Test 13 (TranslateGemma Q5)** |
|--------|---------------------------|--------------------------------|
| Czas | 4:46 | **3:51** (szybciej) |
| Język | PL ✅ | **PL ✅** |
| Nagłówki | ❌ Brak | ** Brak** |
| Błędy słownikowe | "rudy lis" | **"szczur", "łóżko psa", "czarny lis", "łupieżec"** ❌ |
| Jakość | ❌ 66% | **❌ 60%** |

### Wniosek

**PDF potwierdza hipotezę o kumulacji błędów w formatach XHTML:**
- ❌ Najgorsza jakość ze wszystkich testów (60%)
- ❌ Krytyczne błędy słownikowe ("szczur" zamiast "lis", "łóżko" zamiast "nad")
- ❌ Brak nagłówków sekcji (problem z ekstrakcją PDF)
- ✅ Szybszy niż Q4 (3:51 vs 4:46)

**Hipoteza potwierdzona:** Formaty XHTML (HTML, DOCX, ODT, PDF, EPUB) mają systematycznie gorszą jakość z szablonem "translategemma". Chatml + parallel=2 daje lepsze wyniki.

---

## Test 13b: Plik PDF (.pdf) - Gemini 3.5 Flash Lite (chmura)

**Data:** 2026-09-04  
**Czas tłumaczenia:** **1:37 (97s)** 🚀  
**Model:** Gemini 3.5 Flash Lite (chmura Google)  
**Szablon czatu:** N/A (zewnętrzne API)  
**Język docelowy:** Polish  
**Skill PDF:** ✅ włączony  
**Chunk size:** 4000  
**Temperature:** 0.0  
**Glosariusz:** IT  
**Parallel:** 2  
**Status:** ✅ BARDZO DOBRZE - DEKLASUJE TRANSLATEGEMMA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **znacznie lepsza** niż TranslateGemma!

### Porównanie z Testem 13 (TranslateGemma-4B Q5)

| Aspekt | TranslateGemma-4B Q5 (test 13) | **Gemini 3.5 Flash Lite (test 13b)** |
|--------|-------------------------------|--------------------------------------|
| Czas | 3:51 (231s) | **1:37 (97s)** 🚀 (2.4x szybciej!) |
| "To zdanie" | ✅ | **✅** |
| "poranne słońce" |  "słońce poranku" | **✅ "poranne słońce"** |
| "leniwym psem" |  "łagodnym psiem" | **✅ "leniwym psem"** |
| "odległymi wzgórzami" | ✅ | **✅** |
| "Szczur brązowy" | ❌❌ | **✅ "Szybki brązowy lis"** |
| "łóżko psa" | ❌❌ | **✅ "nad leniwym psem"** |
| Nagłówki | ❌ Brak | **❌ Brak** (problem PDF) |
| Jakość | ❌ 60% | **✅ 85%** (poprawa!) |

### Wniosek

**Gemini 3.5 Flash Lite DEKLASUJE TranslateGemma dla PDF:**
-  **2.4x szybszy** (1:37 vs 3:51)
- ✅ **Znacznie lepsza jakość** (85% vs 60%)!
- ✅ **Brak krytycznych błędów** ("Szczur", "łóżko psa")
- ✅ **"poranne słońce"** poprawne
- ❌ Nagłówki nie przetłumaczone (problem z ekstrakcją PDF, nie z modelem)

**To rewelacja!** Gemini radzi sobie z PDF znacznie lepiej niż lokalne modele!

---

## Test 14: Plik EPUB (.epub) - TranslateGemma-4B Q5_K_M + szablon translategemma

**Data:** 2026-09-04  
**Czas tłumaczenia:** 2:58  
**Model:** TranslateGemma-4b-it Q5_K_M (2.7 GB)  
**Szablon czatu:** translategemma (natywny Gemma 3 jinja)  
**Język docelowy:**  TranslateGemma (wykryj + PL) → "auto to pl"  
**Status:** ️ DZIAŁA ALE Z BŁĘDAMI

### Wynik

Tłumaczenie jest **kompletne** (wszystkie 3 sekcje) i po **POLSKU**. Struktura EPUB zachowana.

### ✅ Co działa

- Wszystkie 3 sekcje przetłumaczone (EN, FR, DE)
- Struktura EPUB zachowana
- Język polski ✅
- **Brak wycieku promptu** (poprawa vs Test 7!)

### ⚠️ Problemy

1. **Nagłówki nie przetłumaczone:**
   - "Section Francuska" → "Section Francuska" (brak tłumaczenia!) ❌
   - "Deutscher Abschnitt" → "Deutscher Abschnitt" (brak tłumaczenia!) ❌
2. **"Ta fraza"** zamiast "To zdanie" - powtarza się
3. **"poranek słońce" / "słońce poranka"** - błędy gramatyczne
4. **"leżącym psiem"** - w oryginale "lazy dog" (leniwym psem)
5. **"nad łupieżem psa"** - w oryginale "faulen Hund" (leniwym psem) 
6. **"Ten zdanie"** - błąd gramatyczny
7. **"Szybki brunatny lis skoczył"** - w sekcji FR (powinno być "skacze")

### Porównanie z Testem 7 (TranslateGemma Q4 + auto)

| Aspekt | Test 7 (TranslateGemma Q4) | **Test 14 (TranslateGemma Q5)** |
|--------|---------------------------|--------------------------------|
| Czas | 6:46 | **2:58** (2x szybciej!) |
| Język | PL ✅ | **PL ✅** |
| Wyciek promptu | ❌ Był | **✅ Brak** |
| Nagłówki | ️ Częściowo | **❌ Nie przetłumaczone** |
| Błędy słownikowe | "ta zdanie" | **"łupieżem", "leżącym"** |
| Jakość | ❌ 66% | **⚠️ 65%** |

### Wniosek

**EPUB potwierdza hipotezę o problemach z XHTML:**
- ✅ Brak wycieku promptu (poprawa vs Q4!)
- ✅ 2x szybszy niż Q4 (2:58 vs 6:46)
- ️ Nagłówki nie przetłumaczone (problem z ekstrakcją EPUB)
- ⚠️ Błędy słownikowe ("łupieżem", "leżącym")
- ️ Jakość podobna do Q4 (65% vs 66%)

**Hipoteza potwierdzona:** Szablon "translategemma" nie jest optymalny dla formatów XHTML. Chatml daje lepsze wyniki.

---

## Test 14b: Plik EPUB (.epub) - Gemini 3.5 Flash Lite (chmura)

**Data:** 2026-09-04  
**Czas tłumaczenia:** **36s**   
**Model:** Gemini 3.5 Flash Lite (chmura Google)  
**Szablon czatu:** N/A (zewnętrzne API)  
**Język docelowy:** Polish  
**Skill EPUB:** ✅ włączony  
**Chunk size:** 1000  
**Temperature:** 0.0  
**Glosariusz:** IT  
**Parallel:** 2  
**Status:** ✅ BARDZO DOBRZE - DEKLASUJE TRANSLATEGEMMA!

### Wynik

Tłumaczenie jest **kompletne** i po **POLSKU**. Jakość **znacznie lepsza** niż TranslateGemma!

### Porównanie z Testem 14 (TranslateGemma-4B Q5)

| Aspekt | TranslateGemma-4B Q5 (test 14) | **Gemini 3.5 Flash Lite (test 14b)** |
|--------|-------------------------------|--------------------------------------|
| Czas | 2:58 (178s) | **36s** 🚀 (5x szybciej!) |
| "To zdanie" (EN) | ✅ | **✅** |
| "poranne słońce" |  "poranek słońce" | **✅ "poranne słońce"** |
| "leniwego psa" |  "leżącym/łupieżem" | **✅ "leniwego psa"** |
| "odległymi wzgórzami" | ✅ | **✅** |
| "Section Française" |  Częściowo | **❌ Nie przetłumaczone** |
| "Deutscher Abschnitt" |  | **❌ Nie przetłumaczone** |
| "Ta fraza" (FR) | ✅ "To zdanie" | **❌ "Ta fraza"** (regresja!) |
| "zielonymi wzgórzami" (DE) | ✅ "dalekimi" | **❌ "zielonymi"** (błąd!) |
| Wyciek promptu | ✅ Brak | **✅ Brak** |
| Jakość | ⚠️ 65% | **✅ 80%** (poprawa!) |

### Wniosek

**Gemini 3.5 Flash Lite DEKLASUJE TranslateGemma dla EPUB:**
-  **5x szybszy** (36s vs 2:58)!
- ✅ **Znacznie lepsza jakość** (80% vs 65%)!
- ✅ **Brak wycieku promptu**
- ✅ **"poranne słońce"** poprawne
- ✅ **"leniwego psa"** poprawne
- ❌ Nagłówki nie przetłumaczone (problem z skill EPUB?)
- ️ "Ta fraza" w FR (regresja)
- ️ "zielonymi wzgórzami" w DE (błąd!)

**Gemini radzi sobie z EPUB znacznie lepiej niż lokalne modele!**

---

## Podsumowanie testów Gemini 3.5 Flash Lite (wszystkie formaty):

| Format | Chunk | Czas | Jakość | vs TranslateGemma |
|--------|-------|------|--------|-------------------|
| **ODT** | 1000 | **27s** 🚀 | **85%** 🥇 | 6x szybszy, +7% |
| **PDF** | 4000 | **1:37** 🚀 | **85%** 🥇 | 2.4x szybszy, +25% |
| **EPUB** | 1000 | **36s** 🚀 | **80%** 🥇 | 5x szybszy, +15% |

---

## Podsumowanie końcowe

### Najlepsza konfiguracja (zaktualizowano 2026-09-04)

- **Model:** TranslateGemma-4b-it Q5_K_M
- **Szablon czatu:** translategemma (natywny Gemma 3)
- **Język docelowy:**  TranslateGemma (wykryj + PL)
- **Parallel:** 2
- **Chunk size:** 2000

### Ranking formatów (dla TranslateGemma Q5 + szablon translategemma)

1. **TXT** (85%) - znacząca poprawa z nowym szablonem!
2. **Markdown** (80%) - podobna jakość do Q4
3. **HTML** (80%) - działa ale gorsze niż Q4+chatml (90%)
4. **DOCX** (70%) - działa ale gorsze niż Q4+chatml+parallel=2 (75%)
5. **ODT** (65%) - działa ale gorsze niż Q4 (70%), brak artefaktów XML ✅
6. **EPUB** (65%) - brak wycieku promptu ✅, 2x szybszy niż Q4
7. **PDF** (60%) - najgorszy wynik, krytyczne błędy słownikowe

**Wszystkie formaty testowane z TranslateGemma Q5 + szablon translategemma!**

### Znane problemy (do naprawy w przyszłości)

1. **"Ta zdanie"** w TranslateGemma Q4 (nie występuje w TranslateGemma)
2. **PDF: brak nagłówków** - może wymagać łączenia bloków
3. **EPUB: wyciek promptu** - wymaga naprawy skilla
4. **DOCX: artefakty XML** - wymaga naprawy skilla

### Hipoteza: Kumulacja błędów w formatach XHTML

**Obserwacja (2026-09-04):** Jakość tłumaczenia spada w kolejnych testach z szablonem "translategemma":

| Test | Format | Skill | XHTML | Jakość |
|------|--------|-------|-------|--------|
| 8 | TXT | plaintext | ❌ | **85%** |
| 10 | Markdown | markdown | ❌ | **80%** |
| 9 | HTML | html | ✅ | **80%** |
| 11 | DOCX | docx | ✅ | **70%** |
| 12 | ODT | odt | ✅ | **65%** |

**Hipoteza:** Błędy kumulują się w formatach XHTML (HTML, DOCX, ODT, EPUB).

**Możliwe przyczyny:**
1. **Cache tłumaczeń** - jeśli nie jest czyszczony między testami, błędne tłumaczenia mogą być reused
2. **Context window** - model może "pamiętać" błędy z poprzednich chunków/plików
3. **Skill XHTML** - skills dla formatów binarnych mogą nie chronić wystarczająco przed błędami
4. **Szablon translategemma** - może nie być optymalny dla XHTML (chatml daje lepsze wyniki)

**Test do weryfikacji:**
- Wyczyścić cache przed każdym testem
- Testować formaty XHTML w losowej kolejności (nie sekwencyjnie)
- Porównać chatml vs translategemma dla XHTML

---

### Zmiany wprowadzone w v0.20.1

1. ✅ Wzmocniony prompt główny (reguły gramatyczne)
2. ✅ Auto-odznaczanie skilli przy wyborze pliku
3. ✅ Logowanie postępu bloków ("Ukończono blok X/Y")
4. ✅ Podział glosariusza na kategorie tematyczne
5. ✅ Konwerter TBX → CSV (Microsoft Terminology)

---

**Data zakończenia testów:** 2026-09-03  
**Wersja:** 0.20.1  
**Model zalecany:** TranslateGemma-4b

| Test | Format | Czas | Status | Jakość |
|------|--------|------|--------|--------|
| 1 | .txt | 1:12 | ❌ Niekompletne | 30% |
| 2 | .md | - | - | - |
| 3 | .pdf | - | - | - |
