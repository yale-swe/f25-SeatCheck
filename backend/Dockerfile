FROM python:3.14-slim


# Install curl and ca-certs for tls
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Only copy pyproject.toml (no uv.lock yet)
COPY pyproject.toml ./

# Create the virtualenv + install deps based on pyproject.toml
RUN uv sync

# "source" venv
ENV PATH="/app/.venv/bin:${PATH}"

# Now copy the rest of the backend code
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
