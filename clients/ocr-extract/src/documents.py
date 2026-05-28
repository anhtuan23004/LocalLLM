import mimetypes
from dataclasses import dataclass
from urllib.parse import urlparse

import fitz
import httpx
from fastapi import HTTPException

from .config import env_int


ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | {"application/pdf"}


@dataclass(frozen=True)
class PageImage:
    page_number: int
    content: bytes
    mime_type: str


@dataclass(frozen=True)
class LoadedDocument:
    file_name: str
    mime_type: str
    pages: list[PageImage]

    def pages_by_number(self, page_order: list[int]) -> list[PageImage]:
        page_map = {page.page_number: page for page in self.pages}
        try:
            return [page_map[page_number] for page_number in page_order]
        except KeyError as exc:
            raise ValueError(f"page_order references missing page {exc.args[0]}") from exc


async def load_document(file_url: str) -> LoadedDocument:
    content, file_name, mime_type = await download_file(file_url)
    if mime_type == "application/pdf":
        pages = render_pdf_pages(content)
    else:
        pages = [PageImage(page_number=1, content=content, mime_type=mime_type)]
    return LoadedDocument(file_name=file_name, mime_type=mime_type, pages=pages)


async def download_file(file_url: str) -> tuple[bytes, str, str]:
    timeout = env_int("REQUEST_TIMEOUT_SECONDS", 120)
    max_bytes = env_int("MAX_FILE_BYTES", 50 * 1024 * 1024)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", file_url) as response:
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > max_bytes:
                    raise HTTPException(status_code=413, detail="file exceeds MAX_FILE_BYTES")

                buffer = bytearray()
                async for chunk in response.aiter_bytes():
                    buffer.extend(chunk)
                    if len(buffer) > max_bytes:
                        raise HTTPException(status_code=413, detail="file exceeds MAX_FILE_BYTES")
                content = bytes(buffer)
                content_type = response.headers.get("content-type", "")
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=400, detail=f"failed to download file: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid content-length: {exc}") from exc

    mime_type = clean_mime_type(content_type)
    if mime_type in {"", "application/octet-stream", "binary/octet-stream"}:
        mime_type = guess_mime_type(file_url, content)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"unsupported file content type: {mime_type}")

    parsed_url = urlparse(file_url)
    file_name = parsed_url.path.rsplit("/", 1)[-1] or "downloaded_file"
    return content, file_name[:100], mime_type


def clean_mime_type(content_type: str) -> str:
    return content_type.split(";", 1)[0].strip().lower()


def guess_mime_type(file_url: str, content: bytes) -> str:
    guessed_type, _ = mimetypes.guess_type(urlparse(file_url).path)
    if guessed_type:
        return guessed_type.lower()
    if content.startswith(b"%PDF"):
        return "application/pdf"
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def render_pdf_pages(content: bytes) -> list[PageImage]:
    max_pages = env_int("MAX_PDF_PAGES", 20)
    dpi = env_int("PDF_RENDER_DPI", 144)
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            if len(document) > max_pages:
                raise HTTPException(status_code=413, detail="PDF exceeds MAX_PDF_PAGES")
            pages: list[PageImage] = []
            for index, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(dpi=dpi)
                pages.append(
                    PageImage(
                        page_number=index,
                        content=pixmap.tobytes("png"),
                        mime_type="image/png",
                    )
                )
            return pages
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"failed to render PDF: {exc}") from exc
