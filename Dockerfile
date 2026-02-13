FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project metadata FIRST
COPY pyproject.toml uv.lock README.md ./

# Copy source
COPY src ./src

# Install project + dependencies
RUN uv pip install --system --no-cache .

EXPOSE 8080

CMD ["uvicorn", "hyper_mirror.main:app", "--host", "0.0.0.0", "--port", "8080"]
