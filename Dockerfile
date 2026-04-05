FROM python:3.13-slim

WORKDIR /workspace

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files and install dependencies
COPY . .
RUN uv sync --no-dev

# Flask app port
EXPOSE 5000

# Default to non-debug mode in containers
ENV FLASK_DEBUG=false

# Run the application entrypoint directly (avoids flask reloader/debug process model)
CMD ["uv", "run", "python", "run.py"]