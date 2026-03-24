FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
COPY triplestore/requirements.txt triplestore/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r triplestore/requirements.txt

COPY app/ ./app/
COPY triplestore/ ./triplestore/

# Makes `from routes import ...` work inside main.py
ENV PYTHONPATH=/app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
