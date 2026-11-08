FROM python:3.12-slim

# Runs on arm64 (Pi 5) and amd64 (laptop) from the same manifest.
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pi5-software/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir \
    "fastapi>=0.115" "uvicorn[standard]>=0.32" "paho-mqtt>=2.1" \
    "numpy>=2.0" "pyserial>=3.5"

COPY pi5-software/dashboard.py /app/dashboard.py
COPY pi5-software/mqtt_bridge.py /app/mqtt_bridge.py

RUN useradd --system --uid 10001 telescope && chown -R telescope /app
USER telescope

EXPOSE 8443
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import socket;socket.create_connection(('127.0.0.1',8443),3)"

CMD ["uvicorn", "dashboard:app", "--host", "0.0.0.0", "--port", "8443"]
