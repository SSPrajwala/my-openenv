FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source — following the OpenEnv course 3-component structure:
#   models.py            types (Action / Observation / State)
#   server/environment.py  environment logic
#   server/app.py          FastAPI wiring
#   client.py            HTTP client
#   inference.py         baseline agent script
#   openenv.yaml         environment manifest
COPY models.py .
COPY client.py .
COPY inference.py .
COPY openenv.yaml .
COPY app.py .
COPY server/ ./server/

# HuggingFace Spaces uses port 7860
EXPOSE 7860

# Run the FastAPI server via the server.app module (multi-mode deployment)
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
