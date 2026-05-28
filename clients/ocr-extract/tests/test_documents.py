import fitz
import pytest
from fastapi import HTTPException

from src.documents import render_pdf_pages


def make_pdf(page_count: int) -> bytes:
    document = fitz.open()
    for _ in range(page_count):
        document.new_page(width=72, height=72)
    try:
        return document.write()
    finally:
        document.close()


def test_render_pdf_pages_creates_one_png_per_page(monkeypatch):
    monkeypatch.setenv("MAX_PDF_PAGES", "2")
    pages = render_pdf_pages(make_pdf(2))

    assert [page.page_number for page in pages] == [1, 2]
    assert all(page.mime_type == "image/png" for page in pages)
    assert all(page.content.startswith(b"\x89PNG") for page in pages)


def test_render_pdf_pages_enforces_page_limit(monkeypatch):
    monkeypatch.setenv("MAX_PDF_PAGES", "1")

    with pytest.raises(HTTPException) as exc_info:
        render_pdf_pages(make_pdf(2))

    assert exc_info.value.status_code == 413
