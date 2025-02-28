# Scanner Darkly Video Effect

A deep learning-based implementation of the rotoscoping effect similar to the one used in the movie "A Scanner Darkly". This effect combines neural network edge detection with color quantization to create a distinctive hand-drawn animation look.

## Features

- Neural network-based edge detection using HED (Holistically-Nested Edge Detection)
- Multiple color quantization algorithms (k-means, mean-shift, bilateral filtering)
- Temporal smoothing to reduce flickering between frames
- GPU acceleration for faster processing
- AWS integration for cloud-based video processing
- Both CLI and service modes

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/edgedetectionstudio/scanner-darkly.git
cd scanner-darkly

# Install the package in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Using Docker

```bash
# Build the Docker image
docker build -t scanner-darkly .

# Run the Docker container
docker run --gpus all -v /path/to/videos:/videos scanner-darkly --input /videos/input.mp4 --output /videos/output.mp4
```

## Usage

### Process a Single Video

```bash
# Using the installed package
scanner-darkly --input input.mp4 --output output.mp4

# Using the script directly
python src/main.py --input input.mp4 --output output.mp4
```

### Run as a Service

```bash
# Set required environment variables
export AWS_REGION=us-east-1
export S3_BUCKET_NAME=your-bucket-name
export SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/your-queue-name

# Start the service
scanner-darkly --service

# Or using the script directly
python src/main.py --service
```

## Configuration

Configuration can be provided via a JSON file:

```json
{
  "use_gpu": true,
  "batch_size": 30,
  "output_quality": "high",
  "max_memory_usage_gb": 4,
  "resize_factor": 1.0,
  "scanner_darkly": {
    "edge_strength": 0.8,
    "edge_thickness": 1.5,
    "num_colors": 8,
    "color_method": "kmeans",
    "smoothing": 0.6,
    "saturation": 1.2,
    "temporal_smoothing": 0.3
  }
}
```

Pass the configuration file using the `--config` parameter:

```bash
scanner-darkly --config config.json --input input.mp4 --output output.mp4
```

## AWS Integration

The service integrates with AWS S3 and SQS to process videos in the cloud:

1. Upload a video to S3
2. Send a message to SQS with the following format:
   ```json
   {
     "bucket": "your-bucket-name",
     "input_key": "uploads/your-video.mp4",
     "output_key": "processed/your-video.mp4",
     "effect_type": "scanner_darkly"
   }
   ```
3. The service will download the video, process it, and upload the result back to S3

## Requirements

- Python 3.7+
- OpenCV
- PyTorch
- FFmpeg
- CUDA-capable GPU (for optimal performance)

## License

MIT License