FROM python:3.12.2-slim-bullseye

RUN apt update && apt install -y curl vim

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /app
RUN chmod -R 777 /app

COPY pyproject.toml /app/
COPY poetry.lock /app/

RUN poetry install
RUN pip install schedule

COPY waap/handler /app/waap/handler
COPY waap/middleware /app/waap/middleware


CMD ["uvicorn", "waap.handler.main:app", "--host", "0.0.0.0", "--port", "8008"]
