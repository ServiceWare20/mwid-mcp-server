FROM python:3.13-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY MWAP_MCPserver.py .
COPY serve.py .
COPY .env .

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Run the server
CMD ["python", "serve.py"]
