FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir streamlit==1.32.2 pandas matplotlib plotly

# Copy project files
COPY chatbi_frontend.py .
COPY chatbi-application ./chatbi-application
COPY pipeline_frontend.py .
COPY Ecommerce.db .

# Create the Streamlit config directory
RUN mkdir -p /app/.streamlit
COPY .streamlit/config.toml /app/.streamlit/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "chatbi_frontend.py"]
