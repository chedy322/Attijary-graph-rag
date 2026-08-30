<!-- RUN THIS FOR CELERY -->
celery -A celery_worker.celery_app worker --loglevel=info --pool=threads

<!-- DOCKER -->
docker compose up -d

<!-- INFRASTRUCTURE -->
terraform apply -auto-approve



<!-- NOTE FOR PDF  -->

1. OS-Level Binaries (System Level)
If any of these 4 system dependencies are missing, unstructured will crash at runtime:

Poppler (poppler-utils / pdftoppm): Converts PDF pages into image buffers.

Tesseract OCR (tesseract-ocr): Performs OCR on scanned PDFs and images.

Libmagic (libmagic1): Used by unstructured auto-detection to identify MIME file types (most common next crash if missing).

OpenCV GUI Libraries (libgl1, libglib2.0-0): Needed for table extraction, image cropping, and layout analysis models.

2. Production-Ready Dockerfile (Includes All System Binaries)
Running this inside Docker eliminates Windows environment variables and OS mismatch bugs completely:

Dockerfile
FROM python:3.12-slim

# Install ALL required OS-level dependencies for Unstructured & PDF OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    libmagic1 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*






