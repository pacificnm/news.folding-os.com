FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./

# foldingos-api-core is a private repo; the GitHub PAT is injected as a
# BuildKit secret, used only for this single layer, and unset before the
# layer is committed so it never lands in the image:
#   docker build --secret id=github_token,env=GITHUB_TOKEN .
RUN --mount=type=secret,id=github_token \
    git config --global url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf "https://github.com/" \
    && pip install --no-cache-dir -r requirements.txt \
    && git config --global --unset url."https://$(cat /run/secrets/github_token)@github.com/".insteadOf

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
