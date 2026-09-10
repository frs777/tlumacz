"""Testy modułu pdf_extractor — ekstrakcja tekstu z PDF z zachowaniem pozycji.

Moduł pdf_extractor.py nie miał wcześniej testów. Te testy weryfikują:
- Poprawność ekstrakcji bloków tekstu
- Poprawność ekstrakcji informacji o PDF
- Edge cases (pusty PDF, PDF z obrazkami)
- Strukturę danych TextSpan i TextBlock
"""

import pytest
from pathlib import Path
import fitz  # PyMuPDF


@pytest.fixture
def sample_pdf(tmp_path):
    """Tworzy przykładowy PDF z tekstem do testów."""
    pdf_path = tmp_path / "sample.pdf"
    
    doc = fitz.open()
    
    # Strona 1: prosty tekst
    page1 = doc.new_page()
    page1.insert_text((72, 72), "Hello World", fontsize=12)
    page1.insert_text((72, 100), "This is a test PDF document.", fontsize=10)
    
    # Strona 2: tekst w języku polskim
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Przykładowy tekst", fontsize=12)
    page2.insert_text((72, 100), "To jest dokument testowy.", fontsize=10)
    
    doc.save(str(pdf_path))
    doc.close()
    
    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path):
    """Tworzy pusty PDF (bez tekstu)."""
    pdf_path = tmp_path / "empty.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    # Nie dodajemy tekstu
    
    doc.save(str(pdf_path))
    doc.close()
    
    return pdf_path


@pytest.fixture
def image_pdf(tmp_path):
    """Tworzy PDF z samym obrazkiem (bez tekstu)."""
    pdf_path = tmp_path / "image.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    
    # Dodaj prosty obrazek (1x1 pixel)
    img = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 1, 1))
    img.set_rect(img.irect, (255, 0, 0))  # czerwony
    page.insert_image(page.rect, pixmap=img)
    
    doc.save(str(pdf_path))
    doc.close()
    
    return pdf_path


class TestExtractTextBlocks:
    """Testy funkcji extract_text_blocks()."""

    def test_extract_from_sample_pdf(self, sample_pdf):
        """Powinien ekstrahować bloki tekstu z przykładowego PDF."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        blocks = extract_text_blocks(sample_pdf)
        
        # Powinny być co najmniej 4 bloki (2 na stronie × 2 strony)
        assert len(blocks) >= 4, f"Oczekiwano >=4 bloków, otrzymano {len(blocks)}"
        
        # Sprawdź że bloki mają tekst
        all_text = ' '.join(block.text for block in blocks)
        assert "Hello World" in all_text
        # PyMuPDF może nie poprawnie renderować polskich znaków (ł → ·)
        # więc sprawdzamy tylko "Przy" lub "tekst"
        assert "Przy" in all_text or "tekst" in all_text

    def test_block_structure(self, sample_pdf):
        """Bloki powinny mieć poprawną strukturę (spans, page_num, bbox)."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        blocks = extract_text_blocks(sample_pdf)
        
        for block in blocks:
            # TextBlock powinien mieć spans
            assert hasattr(block, 'spans')
            assert isinstance(block.spans, list)
            
            # Każdy span powinien mieć tekst i pozycję
            for span in block.spans:
                assert hasattr(span, 'text')
                assert hasattr(span, 'page_num')
                assert hasattr(span, 'x0')
                assert hasattr(span, 'y0')
                assert hasattr(span, 'x1')
                assert hasattr(span, 'y1')
                assert hasattr(span, 'font_size')
                assert hasattr(span, 'font_name')
                
                # Pozycje powinny być liczbami
                assert isinstance(span.x0, (int, float))
                assert isinstance(span.y0, (int, float))
                assert isinstance(span.font_size, (int, float))

    def test_page_numbers(self, sample_pdf):
        """Numery stron powinny być 0-indexed."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        blocks = extract_text_blocks(sample_pdf)
        
        page_nums = set(block.page_num for block in blocks)
        
        # Powinny być strony 0 i 1 (2 strony)
        assert 0 in page_nums, "Brak bloków ze strony 0"
        assert 1 in page_nums, "Brak bloków ze strony 1"

    def test_empty_pdf(self, empty_pdf):
        """Pusty PDF powinien zwrócić pustą listę bloków."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        blocks = extract_text_blocks(empty_pdf)
        
        assert len(blocks) == 0, f"Oczekiwano 0 bloków dla pustego PDF, otrzymano {len(blocks)}"

    def test_image_pdf(self, image_pdf):
        """PDF z samym obrazkiem powinien zwrócić pustą listę bloków."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        blocks = extract_text_blocks(image_pdf)
        
        # Obrazki są pomijane (type=1), więc nie powinno być bloków tekstu
        assert len(blocks) == 0, f"Oczekiwano 0 bloków dla PDF z obrazkiem, otrzymano {len(blocks)}"

    def test_text_property(self, sample_pdf):
        """Właściwość text powinna zwracać połączony tekst ze wszystkich spans."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        blocks = extract_text_blocks(sample_pdf)
        
        for block in blocks:
            # block.text powinno być równe ''.join(span.text for span in block.spans)
            expected_text = ''.join(span.text for span in block.spans)
            assert block.text == expected_text


class TestGetPdfInfo:
    """Testy funkcji get_pdf_info()."""

    def test_get_info_sample_pdf(self, sample_pdf):
        """Powinien zwrócić informacje o przykładowym PDF."""
        from tlumacz.pdf_extractor import get_pdf_info
        
        info = get_pdf_info(sample_pdf)
        
        assert 'page_count' in info
        assert 'metadata' in info
        
        # 2 strony
        assert info['page_count'] == 2
        
        # Metadata powinno być słownikiem
        assert isinstance(info['metadata'], dict)

    def test_get_info_empty_pdf(self, empty_pdf):
        """Pusty PDF powinien mieć 1 stronę."""
        from tlumacz.pdf_extractor import get_pdf_info
        
        info = get_pdf_info(empty_pdf)
        
        assert info['page_count'] == 1


class TestPdfExtractorEdgeCases:
    """Testy edge cases i obsługi błędów."""

    def test_nonexistent_pdf(self, tmp_path):
        """Nieistniejący PDF powinien rzucić wyjątek."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        nonexistent = tmp_path / "nonexistent.pdf"
        
        with pytest.raises(Exception):  # fitz.FileDataError lub FileNotFoundError
            extract_text_blocks(nonexistent)

    def test_invalid_pdf(self, tmp_path):
        """Nieprawidłowy plik PDF powinien rzucić wyjątek."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        invalid_pdf = tmp_path / "invalid.pdf"
        invalid_pdf.write_text("To nie jest PDF")
        
        with pytest.raises(Exception):
            extract_text_blocks(invalid_pdf)

    def test_path_object(self, sample_pdf):
        """Funkcja powinna akceptować Path object (nie tylko string)."""
        from tlumacz.pdf_extractor import extract_text_blocks
        
        # sample_pdf to Path object
        assert isinstance(sample_pdf, Path)
        
        blocks = extract_text_blocks(sample_pdf)
        assert len(blocks) > 0


class TestTextSpanAndTextBlock:
    """Testy struktur danych TextSpan i TextBlock."""

    def test_textspan_creation(self):
        """TextSpan powinien być tworzony poprawnie."""
        from tlumacz.pdf_extractor import TextSpan
        
        span = TextSpan(
            text="Hello",
            page_num=0,
            x0=10.0,
            y0=20.0,
            x1=50.0,
            y1=30.0,
            font_size=12.0,
            font_name="Helvetica",
        )
        
        assert span.text == "Hello"
        assert span.page_num == 0
        assert span.font_size == 12.0
        assert span.font_name == "Helvetica"

    def test_textblock_creation(self):
        """TextBlock powinien być tworzony poprawnie."""
        from tlumacz.pdf_extractor import TextBlock, TextSpan
        
        span1 = TextSpan("Hello ", 0, 10, 20, 50, 30, 12, "Helvetica")
        span2 = TextSpan("World", 0, 50, 20, 90, 30, 12, "Helvetica")
        
        block = TextBlock(
            spans=[span1, span2],
            page_num=0,
            x0=10,
            y0=20,
            x1=90,
            y1=30,
        )
        
        assert len(block.spans) == 2
        assert block.text == "Hello World"
        assert block.page_num == 0
