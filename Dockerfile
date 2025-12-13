FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# System deps for OCR, PDF, OpenCV, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    swig \
    pkg-config \
    git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.minimal.txt .
RUN pip install --no-cache-dir -r requirements.minimal.txt

COPY . .

# Ensure demo feeds directory exists in final image (used for crawler fallbacks)
RUN mkdir -p /app/data/feeds

# Optional: empty GeM API key triggers demo fallback automatically
ENV GEM_API_KEY=""

ENV ENVIRONMENT=production
ENV DEBUG=false

EXPOSE 8000

# Run API by default; pipeline can be run with `docker run ... python main.py`
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
