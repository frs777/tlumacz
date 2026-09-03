"""Ekstrakcja tekstu z PDF z zachowaniem pozycji.

Moduł używa PyMuPDF (fitz) do ekstrakcji tekstu z PDF z informacją o pozycjach,
stronach i rozmiarach czcionek. Pozwala na tłumaczenie tekstu z zachowaniem
układu PDF.

Architektura przygotowana pod przyszłe dodanie OCR.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


@dataclass
class TextSpan:
    """Fragment tekstu z pozycją i formatowaniem."""
    text: str
    page_num: int  # numer strony (0-indexed)
    x0: float  # lewa krawędź
    y0: float  # górna krawędź
    x1: float  # prawa krawędź
    y1: float  # dolna krawędź
    font_size: float  # rozmiar czcionki
    font_name: str  # nazwa czcionki


@dataclass
class TextBlock:
    """Blok tekstu (akapit) z pozycją."""
    spans: list[TextSpan]  # fragmenty tekstu w bloku
    page_num: int  # numer strony (0-indexed)
    x0: float  # lewa krawędź bloku
    y0: float  # górna krawędź bloku
    x1: float  # prawa krawędź bloku
    y1: float  # dolna krawędź bloku

    @property
    def text(self) -> str:
        """Połączony tekst ze wszystkich fragmentów."""
        return ''.join(span.text for span in self.spans)


def extract_text_blocks(pdf_path: str | Path) -> list[TextBlock]:
    """Ekstrahuje bloki tekstu z PDF z pozycjami.

    Args:
        pdf_path: Ścieżka do pliku PDF.

    Returns:
        Lista bloków tekstu z pozycjami i formatowaniem.
    """
    doc = fitz.open(str(pdf_path))
    blocks: list[TextBlock] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_dict = page.get_text('dict')

        for block in page_dict['blocks']:
            # Pomijamy bloki obrazków (type=1)
            if block['type'] != 0:  # 0 = tekst, 1 = obrazek
                continue

            spans: list[TextSpan] = []
            block_x0 = block['bbox'][0]
            block_y0 = block['bbox'][1]
            block_x1 = block['bbox'][2]
            block_y1 = block['bbox'][3]

            for line in block['lines']:
                for span in line['spans']:
                    text = span['text']
                    # Pomijamy puste fragmenty
                    if not text.strip():
                        continue

                    text_span = TextSpan(
                        text=text,
                        page_num=page_num,
                        x0=span['bbox'][0],
                        y0=span['bbox'][1],
                        x1=span['bbox'][2],
                        y1=span['bbox'][3],
                        font_size=span['size'],
                        font_name=span['font'],
                    )
                    spans.append(text_span)

            # Dodajemy blok tylko jeśli ma jakieś fragmenty
            if spans:
                text_block = TextBlock(
                    spans=spans,
                    page_num=page_num,
                    x0=block_x0,
                    y0=block_y0,
                    x1=block_x1,
                    y1=block_y1,
                )
                blocks.append(text_block)

    doc.close()
    return blocks


def get_pdf_info(pdf_path: str | Path) -> dict:
    """Zwraca informacje o PDF.

    Args:
        pdf_path: Ścieżka do pliku PDF.

    Returns:
        Słownik z informacjami o PDF (liczba stron, autor, tytuł, itp.).
    """
    doc = fitz.open(str(pdf_path))
    info = {
        'page_count': len(doc),
        'metadata': doc.metadata,
    }
    doc.close()
    return info
