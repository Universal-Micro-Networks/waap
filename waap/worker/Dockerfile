FROM python:3.12.2-slim-bullseye

RUN apt update && apt install -y curl vim

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install

COPY waap/worker /app/waap/worker
COPY waap/middleware /app/waap/middleware


CMD ["uvicorn", "waap.worker.main:app", "--host", "0.0.0.0", "--port", "8088"]
