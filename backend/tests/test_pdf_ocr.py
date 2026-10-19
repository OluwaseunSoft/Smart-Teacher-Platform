from __future__ import annotations

import io
import subprocess
import struct

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject, NumberObject

from app.services import ingestion, ocr


def scanned_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    page = writer.add_blank_page(width=72, height=72)
    image = DecodedStreamObject()
    image.set_data(b"\xff\xff\xff")
    image.update({
        NameObject("/Type"): NameObject("/XObject"),
        NameObject("/Subtype"): NameObject("/Image"),
        NameObject("/Width"): NumberObject(1), NameObject("/Height"): NumberObject(1),
        NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
        NameObject("/BitsPerComponent"): NumberObject(8),
    })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/XObject"): DictionaryObject({NameObject("/Scan"): writer._add_object(image)}),
    })
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_scanned_page_ocr_keeps_page_positions(monkeypatch):
    calls = []

    def recognize(data, indices):
        calls.append(indices)
        return {1: "العادات الذرية"}

    monkeypatch.setattr(ocr, "recognize_pages", recognize)
    assert ingestion.extract_pdf_pages(scanned_pdf()) == ["", "العادات الذرية"]
    assert calls == [[1]]


def test_blank_pdf_does_not_require_ocr(monkeypatch):
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    buffer = io.BytesIO()
    writer.write(buffer)
    monkeypatch.setattr(ocr, "recognize_pages", lambda *args: pytest.fail("Blank pages need no OCR"))
    assert ingestion.extract_pdf_pages(buffer.getvalue()) == [""]


def test_mixed_pdf_preserves_existing_text(monkeypatch):
    from types import SimpleNamespace
    import pypdf

    pages = [
        SimpleNamespace(extract_text=lambda: "Existing digital text", images=[1]),
        SimpleNamespace(extract_text=lambda: "", images=[1]),
    ]
    monkeypatch.setattr(pypdf, "PdfReader", lambda *args: SimpleNamespace(pages=pages))
    def recognize(data, indices):
        assert indices == [1]
        return {1: "نص عربي"}
    monkeypatch.setattr(ocr, "recognize_pages", recognize)
    assert ingestion.extract_pdf_pages(b"mixed") == ["Existing digital text", "نص عربي"]


def test_unreadable_scan_returns_clear_error(monkeypatch):
    monkeypatch.setattr(ocr, "recognize_pages", lambda *args: {1: ""})
    with pytest.raises(ValueError, match="OCR could not read"):
        ingestion.extract_pdf_pages(scanned_pdf())


def test_pdf_render_produces_valid_bmp(tmp_path):
    image = tmp_path / "page.bmp"
    ocr._render_page(scanned_pdf(), 1, image)
    data = image.read_bytes()
    assert data[:2] == b"BM"
    assert struct.unpack_from("<I", data, 2)[0] == len(data)
    assert struct.unpack_from("<ii", data, 18) == (200, 200)
    assert struct.unpack_from("<H", data, 28)[0] == 24


def test_scanned_upload_saves_recognized_pages(api_client, monkeypatch, test_session):
    from app.models import Material

    signup = api_client.post("/api/auth/signup", json={
        "email": "ocr@example.com", "password": "password123", "display_name": "Reader",
    })
    monkeypatch.setattr(ocr, "recognize_pages", lambda *args: {1: "العادات الذرية"})
    response = api_client.post("/api/materials", headers={
        "Authorization": f"Bearer {signup.json()['access_token']}",
    }, files={"file": ("book.pdf", scanned_pdf(), "application/pdf")})
    assert response.status_code == 201
    material = test_session.get(Material, response.json()["id"])
    assert material.raw_text == "العادات الذرية"
    assert material.raw_pages == ["", "العادات الذرية"]


def test_missing_language_data_fails_before_rendering(monkeypatch):
    monkeypatch.setattr(ocr, "_command", lambda: "tesseract")
    monkeypatch.setattr(ocr, "_run", lambda *args, **kwargs: "List of languages:\neng\n")
    monkeypatch.setattr(ocr.settings, "OCR_LANGUAGES", "ara+eng")
    monkeypatch.setattr(ocr, "_render_page", lambda *args: pytest.fail("Must fail before rendering"))
    with pytest.raises(ValueError, match="language data: ara"):
        ocr.recognize_pages(b"pdf", [0])


def test_ocr_timeout_returns_actionable_error(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("tesseract", 1)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(ValueError, match="smaller chapter"):
        ocr._run(["tesseract"], timeout=1)


def test_ocr_preserves_unicode_and_cleans_temporary_files(monkeypatch):
    paths = []
    monkeypatch.setattr(ocr, "_command", lambda: "tesseract")
    monkeypatch.setattr(ocr.settings, "OCR_LANGUAGES", "ara+eng")

    def render(data, index, path):
        paths.append(path)
        path.write_bytes(b"image")

    def run(command, **kwargs):
        return "ara\neng" if "--list-langs" in command else "نص عربي\n"

    monkeypatch.setattr(ocr, "_render_page", render)
    monkeypatch.setattr(ocr, "_run", run)
    assert ocr.recognize_pages(b"pdf", [2, 5]) == {2: "نص عربي", 5: "نص عربي"}
    assert all(not path.exists() for path in paths)
