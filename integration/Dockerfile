# Use an official Python runtime as a parent image
FROM python:3.12-slim

LABEL name="Sales Agent Integration"

# Set the working directory in the container
WORKDIR /app

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the dependencies files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "uvicorn", "shopify.main:app", "--host", "0.0.0.0", "--port", "8000"]
