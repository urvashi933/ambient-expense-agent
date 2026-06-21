# Use the official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install uv package manager
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY expense_agent/ ./expense_agent/

# Install dependencies using uv
RUN uv sync --frozen

# Expose Cloud Run port
EXPOSE 8080

# Environment variables for production
ENV ADK_FORCE_LOCAL_STORAGE=0
ENV GOOGLE_CLOUD_LOCATION=global

# Run ADK Web server on 8080 and enable pubsub triggers
CMD ["uv", "run", "adk", "web", "expense_agent", "--host", "0.0.0.0", "--port", "8080", "--trigger_sources", "pubsub"]
