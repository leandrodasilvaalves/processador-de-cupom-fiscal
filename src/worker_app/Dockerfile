FROM python:3.11-slim

WORKDIR /app/src

COPY ./src/worker_app/requirements.txt ./worker_app/
RUN pip install --no-cache-dir -r ./worker_app/requirements.txt

COPY ./src/config ./config
COPY ./src/database ./database
COPY ./src/helpers ./helpers
COPY ./src/services ./services
COPY ./src/worker_app ./worker_app

ENV PYTHONPATH=/app/src
WORKDIR /app

CMD ["python", "./src/worker_app/program.py"]