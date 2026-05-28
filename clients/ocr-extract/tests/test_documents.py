import asyncio

import fitz
import httpx
import pytest
from fastapi import HTTPException

from src import documents
from src.documents import download_file, render_pdf_pages, validate_public_http_url


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


def test_validate_public_http_url_rejects_private_resolutions(monkeypatch):
    monkeypatch.setattr(
        documents,
        "resolve_host_addresses",
        lambda host, port: {"127.0.0.1"},
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_public_http_url("https://example.com/file.pdf")

    assert exc_info.value.status_code == 400
    assert "private or reserved" in exc_info.value.detail


def test_validate_public_http_url_rejects_invalid_ports():
    with pytest.raises(HTTPException) as exc_info:
        validate_public_http_url("https://example.com:not-a-port/file.pdf")

    assert exc_info.value.status_code == 400
    assert "port" in exc_info.value.detail


def test_download_file_rejects_redirect_to_private_url(monkeypatch):
    monkeypatch.setattr(
        documents,
        "resolve_host_addresses",
        lambda host, port: {"127.0.0.1"} if host == "127.0.0.1" else {"93.184.216.34"},
    )
    monkeypatch.setattr(
        documents.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(
            [
                FakeResponse(
                    "https://example.com/file.pdf",
                    302,
                    headers={"location": "http://127.0.0.1/internal.pdf"},
                )
            ]
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(download_file("https://example.com/file.pdf"))

    assert exc_info.value.status_code == 400
    assert "private or reserved" in exc_info.value.detail


def test_download_file_maps_upstream_5xx_to_bad_gateway(monkeypatch):
    monkeypatch.setattr(
        documents,
        "resolve_host_addresses",
        lambda host, port: {"93.184.216.34"},
    )
    monkeypatch.setattr(
        documents.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient([FakeResponse("https://example.com/file.pdf", 503)]),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(download_file("https://example.com/file.pdf"))

    assert exc_info.value.status_code == 502
    assert "upstream returned 503" in exc_info.value.detail


def test_download_file_maps_timeout_to_gateway_timeout(monkeypatch):
    monkeypatch.setattr(
        documents,
        "resolve_host_addresses",
        lambda host, port: {"93.184.216.34"},
    )
    request = httpx.Request("GET", "https://example.com/file.pdf")
    monkeypatch.setattr(
        documents.httpx,
        "AsyncClient",
        lambda **kwargs: FakeAsyncClient(
            [httpx.TimeoutException("timed out", request=request)]
        ),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(download_file("https://example.com/file.pdf"))

    assert exc_info.value.status_code == 504


class FakeAsyncClient:
    def __init__(self, responses):
        self.responses = list(responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def stream(self, method, url):
        assert method == "GET"
        return FakeStream(self.responses.pop(0))


class FakeStream:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    async def __aexit__(self, exc_type, exc, traceback):
        return False


class FakeResponse:
    def __init__(self, url, status_code, *, headers=None, chunks=None):
        request = httpx.Request("GET", url)
        self._response = httpx.Response(
            status_code,
            request=request,
            headers=headers or {},
        )
        self.status_code = status_code
        self.url = self._response.url
        self.headers = self._response.headers
        self.chunks = chunks or [b"%PDF-1.7"]

    def raise_for_status(self):
        self._response.raise_for_status()

    async def aiter_bytes(self):
        for chunk in self.chunks:
            yield chunk
