# ═══════════════════════════════════════════════════════════════════════════
# DIGITAL DENIS — Telegram Bot Dockerfile
# ═══════════════════════════════════════════════════════════════════════════

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies (for pydub audio processing)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default command
CMD ["python", "bot.py"]
