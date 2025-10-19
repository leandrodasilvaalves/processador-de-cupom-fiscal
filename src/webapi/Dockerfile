FROM python:3.11-slim

WORKDIR /app/src

COPY ./src/webapi/requirements.txt ./webapi/
RUN pip install --no-cache-dir -r ./webapi/requirements.txt

COPY ./src/config ./config
COPY ./src/database ./database
COPY ./src/helpers ./helpers
COPY ./src/services ./services
COPY ./src/webapi ./webapi

ENV PYTHONPATH=/app/src
WORKDIR /app
EXPOSE 8000

CMD ["uvicorn", "src.webapi.program:app", "--host", "0.0.0.0", "--port", "8000"]