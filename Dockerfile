FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# App Runner will hit port 8000 by default if you set it in the console
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]