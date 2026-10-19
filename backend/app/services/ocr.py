"""Local OCR for scanned PDF pages. No document data is sent to an AI service."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import struct
import subprocess
from tempfile import TemporaryDirectory
from threading import Lock
import time

from app.config import settings

# PDFium is not thread safe, including calls on different documents.
_PDFIUM_LOCK = Lock()


def _command() -> str:
    if settings.OCR_TESSERACT_CMD:
        return settings.OCR_TESSERACT_CMD
    executable = shutil.which("tesseract")
    if executable:
        return executable
    windows_path = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Tesseract-OCR/tesseract.exe"
    if windows_path.is_file():
        return str(windows_path)
    raise ValueError(
        "This PDF contains scanned images. Install Tesseract OCR with Arabic "
        "and English language data, then restart the backend. "
        "See the scanned PDF setup in README.md."
    )


def _run(command: list[str], *, timeout: float) -> str:
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            env={**os.environ, "OMP_THREAD_LIMIT": "2"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(
            "Scanned PDF recognition could not finish. Check the Tesseract OCR "
            "installation or try uploading a smaller chapter."
        ) from exc
    if result.returncode:
        raise ValueError(
            "Scanned PDF recognition failed. Check that Tesseract OCR has the "
            f"configured language data ({settings.OCR_LANGUAGES})."
        )
    return result.stdout


def _render_page(data: bytes, page_index: int, image_path: Path) -> None:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover
        raise ValueError("Install the backend requirements to enable scanned PDF recognition.") from exc
    with _PDFIUM_LOCK:
        document = pdfium.PdfDocument(data)
        try:
            page = document[page_index]
            try:
                width, height = page.get_size()
                scale = min(200 / 72, (12_000_000 / max(1, width * height)) ** 0.5)
                bitmap = page.render(scale=scale, force_bitmap_format=pdfium.raw.FPDFBitmap_BGR)
                try:
                    # A standard 24-bit BMP avoids an additional image-library
                    # dependency. BMP stores BGR rows bottom-up, padded to 4 bytes.
                    row_size = (bitmap.width * 3 + 3) & ~3
                    size = row_size * bitmap.height
                    pixels = bytes(bitmap.buffer)
                    with image_path.open("wb") as output:
                        output.write(struct.pack("<2sIHHI", b"BM", 54 + size, 0, 0, 54))
                        output.write(struct.pack(
                            "<IiiHHIIiiII", 40, bitmap.width, bitmap.height,
                            1, 24, 0, size, 7874, 7874, 0, 0,
                        ))
                        padding = b"\0" * (row_size - bitmap.width * 3)
                        for row in range(bitmap.height - 1, -1, -1):
                            start = row * bitmap.stride
                            output.write(pixels[start:start + bitmap.width * 3])
                            output.write(padding)
                finally:
                    bitmap.close()
            finally:
                page.close()
        finally:
            document.close()


def recognize_pages(data: bytes, page_indices: list[int]) -> dict[int, str]:
    """Recognize selected pages sequentially with bounded memory and time."""
    command = _command()
    extra = ["--tessdata-dir", settings.OCR_TESSDATA_DIR] if settings.OCR_TESSDATA_DIR else []
    languages = set(_run([command, "--list-langs", *extra], timeout=15).splitlines())
    missing = set(settings.OCR_LANGUAGES.split("+")) - languages
    if missing:
        raise ValueError(
            "Scanned PDF recognition needs Tesseract language data: "
            + ", ".join(sorted(missing))
            + ". Install the missing language data and retry."
        )
    deadline = time.monotonic() + settings.OCR_DOCUMENT_TIMEOUT_SECONDS
    result: dict[int, str] = {}
    with TemporaryDirectory(prefix="suhail-ocr-") as directory:
        image_path = Path(directory) / "page.bmp"
        for index in page_indices:
            if time.monotonic() >= deadline:
                raise ValueError("Scanned PDF recognition took too long. Upload a smaller chapter and retry.")
            _render_page(data, index, image_path)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ValueError("Scanned PDF recognition took too long. Upload a smaller chapter and retry.")
            result[index] = _run(
                [command, str(image_path), "stdout", "-l", settings.OCR_LANGUAGES, *extra, "--dpi", "200"],
                timeout=min(settings.OCR_PAGE_TIMEOUT_SECONDS, remaining),
            ).strip()
    return result
