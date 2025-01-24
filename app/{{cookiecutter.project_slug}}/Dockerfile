FROM python:3.11-slim AS requirements-stage
LABEL MAINTAINER="fr.dgc.ops.dgtl@devoteamgcloud.com"

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --dev

# ---
FROM python:3.11-slim

RUN apt-get update && apt-get install git-all -y

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install debugpy && \
    pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./ /code

CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]