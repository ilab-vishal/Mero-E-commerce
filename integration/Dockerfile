# Use official Python 3.12 slim image with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

LABEL name="E-commerce Integration Platform"

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy project configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --no-install-project --no-dev

# Copy project files
COPY . .

# Install the project itself
RUN uv sync --no-dev

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["/app/.venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
