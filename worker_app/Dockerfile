FROM python:3.11-slim

WORKDIR /app

COPY ./worker_app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./worker_app .

CMD ["python", "program.py"]