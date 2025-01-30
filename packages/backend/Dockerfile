FROM python:3.11-slim
ARG TARGETARCH=amd64
ARG TARGETOS=linux

# Install system dependencies including FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt boto3

# Copy source files
COPY src /app/src

# Run the processor
CMD ["python", "src/processor.py"]