FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY services/booking/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Copy application code
COPY services/booking/ .
COPY shared/ ./shared/

ENTRYPOINT ["entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
