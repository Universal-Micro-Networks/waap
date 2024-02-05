FROM python:3.12.0-slim-bullseye

RUN apt update && apt install -y curl vim

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry install --no-root

COPY . /app

CMD ["python", "main.py"]
