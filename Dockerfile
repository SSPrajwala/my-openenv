FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY email_triage_env.py .
COPY server.py .
COPY inference.py .
COPY openenv.yaml .

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Run FastAPI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
