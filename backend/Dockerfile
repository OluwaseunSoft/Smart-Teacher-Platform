FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SEED_DEMO_DATA=true

WORKDIR /app

COPY requirements.txt .
# Recognition stays local; include both language packs in the image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir /data \
    && chown app:app /data

COPY --chown=app:app app ./app

USER app

# Fail the build if OCR, PDF rendering, or IANA time-zone data is unavailable
# to the same unprivileged user that runs the API.
RUN python -c "import subprocess; import pypdfium2; from zoneinfo import ZoneInfo; ZoneInfo('Africa/Lagos'); languages = subprocess.check_output(['tesseract', '--list-langs'], text=True).splitlines(); assert {'ara', 'eng'} <= set(languages), 'Arabic/English OCR language data is missing'"

ENTRYPOINT ["python", "-m", "app.docker_entrypoint"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
