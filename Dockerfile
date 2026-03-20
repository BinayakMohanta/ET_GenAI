FROM python:3.11-slim

WORKDIR /app

# install build deps and pip packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy application
COPY . .

# recommended to set OLLAMA_URL via env when running in the cloud
ENV OLLAMA_URL=""

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
