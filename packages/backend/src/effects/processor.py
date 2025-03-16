#!/usr/bin/env python3
"""
Video processor for applying effects to uploaded videos
Uses dynamic effect loading from S3 with direct class integration for Scanner Darkly
"""

import os
import sys
import json
import logging
import boto3
import subprocess
import traceback
import uuid
from botocore.exceptions import ClientError
import importlib.util
from typing import Dict, Any, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/video-processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

logger.info(f"************* FROM packages/backend/src/effects/processor.py **********")

def sanitize_paths(input_path: str, output_path: str) -> tuple:
    """
    Ensures that input and output paths are different to avoid FFmpeg in-place errors
    
    Args:
        input_path: Original input path
        output_path: Original output path
        
    Returns:
        Tuple of (sanitized_input_path, sanitized_output_path)
    """
    logger.info(f"Sanitizing paths: input={input_path}, output={output_path}")
    
    # If paths are the same, modify the output path
    if input_path == output_path:
        # Generate a new temp file path with uuid to ensure uniqueness
        dirname = os.path.dirname(output_path)
        basename = os.path.basename(output_path)
        
        # Insert a unique ID before extension
        name, ext = os.path.splitext(basename)
        unique_id = str(uuid.uuid4())[:8]
        new_output_path = os.path.join(dirname, f"{name}-processed-{unique_id}{ext}")
        
        logger.info(f"Paths were identical! Modified output path to: {new_output_path}")
        return input_path, new_output_path
    
    # Paths are already different, return as is
    return input_path, output_path

def import_module_from_path(module_name, file_path):
    """
    Dynamically import a module from a file path
    """
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Failed to import module {module_name} from {file_path}: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def process_scanner_darkly(input_path, output_path):
    """
    Process a video with Scanner Darkly effect using the class directly
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import the Scanner Darkly module
        scanner_darkly_path = "/tmp/video_effects/scanner_darkly.py"
        logger.info(f"Importing Scanner Darkly module from {scanner_darkly_path}")
        
        scanner_darkly = import_module_from_path("scanner_darkly", scanner_darkly_path)
        if not scanner_darkly:
            logger.error("Failed to import Scanner Darkly module")
            return False
            
        # Create effect instance
        effect = scanner_darkly.ScannerDarklyEffect(
            edge_strength=0.9,      # Higher strength for more deliberate lines
            edge_thickness=0.7,     # Slightly thicker lines like the movie
            edge_threshold=0.65,    # Much higher threshold to be more selective
            num_colors=5,           # Fewer colors for more flat regions
            color_method="kmeans",  # For compatibility
            smoothing=0.9,          # Stronger smoothing for flatter regions
            saturation=1.15,        # Slightly enhanced saturation
            temporal_smoothing=0.2, # Reduce flickering between frames
            preserve_black=True     # Using black for edges
        )
        
        # Open the input video
        import cv2
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            logger.error(f"Could not open input video: {input_path}")
            return False
            
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Processing video: {width}x{height} at {fps} fps, {total_frames} frames")
        
        # Create output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            logger.error(f"Could not create output video: {output_path}")
            cap.release()
            return False
            
        # Process frames in batches
        batch_size = 30
        frames = []
        processed_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frames.append(frame)
            
            # Process when batch is full or end of video
            if len(frames) >= batch_size or processed_count + len(frames) >= total_frames:
                # Process batch
                logger.info(f"Processing batch of {len(frames)} frames")
                processed_frames = effect.process_batch(frames)
                
                # Write processed frames
                for processed_frame in processed_frames:
                    out.write(processed_frame)
                    
                # Log progress
                processed_count += len(frames)
                logger.info(f"Processed {processed_count}/{total_frames} frames ({processed_count/total_frames*100:.1f}%)")
                
                # Clear batch
                frames = []
        
        # Clean up
        cap.release()
        out.release()
        
        # Convert to h264 using FFmpeg for better compatibility
        temp_output = f"{output_path}.tmp.mp4"
        ffmpeg_cmd = (
            f'ffmpeg -y -i "{output_path}" -c:v libx264 -pix_fmt yuv420p '
            f'-preset medium -crf 18 "{temp_output}"'
        )
        
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        os.replace(temp_output, output_path)
        
        logger.info(f"Successfully processed video with Scanner Darkly effect: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing Scanner Darkly effect: {str(e)}")
        logger.error(traceback.format_exc())
        return False

class VideoProcessor:
    """Main video processor that handles video processing requests"""
    
    def __init__(self, bucket_name, effects_prefix="effects/", core_module_path=None):
        """
        Initialize the video processor
        
        Args:
            bucket_name: S3 bucket name
            effects_prefix: Prefix for effects in S3
            core_module_path: Path to the effect_core.py module
        """
        self.bucket_name = bucket_name
        self.effects_prefix = effects_prefix
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.sqs_client = boto3.client('sqs', region_name='us-east-1')
        
        # Load the core module
        if core_module_path and os.path.exists(core_module_path):
            self.core_module = import_module_from_path("effect_core", core_module_path)
            logger.info(f"Loaded effect core module from {core_module_path}")
        else:
            # Try to download it from S3
            local_core_path = self.download_core_module()
            if local_core_path:
                self.core_module = import_module_from_path("effect_core", local_core_path)
                logger.info(f"Loaded effect core module from {local_core_path}")
            else:
                logger.error("Failed to load effect core module")
                self.core_module = None
        
        # Initialize the effect registry if core module loaded successfully
        if self.core_module:
            self.registry = self.core_module.EffectRegistry(
                s3_bucket=self.bucket_name,
                effects_prefix=self.effects_prefix
            )
            # Pre-load the manifest
            self.registry.load_manifest()
        else:
            self.registry = None
            
    def process_message(self, message):
        """
        Process a message from SQS
        
        Args:
            message: Message dictionary from SQS
            
        Returns:
            True if successful, False otherwise
        """
        try:
            body = json.loads(message['Body'])
            logger.info(f"Processing message: {json.dumps(body, indent=2)}")
            
            # Extract user ID and other parameters
            bucket = body.get('bucket')
            input_key = body.get('input_key')
            output_key = body.get('output_key')
            effect_type = body.get('effect_type', 'silent-movie')
            user_id = body.get('user_id', 'anonymous')  # Default to anonymous if missing
            original_filename = body.get('original_filename', os.path.basename(input_key))
            
            # Validate required fields
            if not bucket or not input_key or not output_key:
                logger.error(f"Message is missing required fields: {body}")
                return False
            
            # Create temporary file paths
            input_filename = os.path.basename(input_key)
            output_filename = os.path.basename(output_key)
            
            # Check if we have the correct folder structure
            if not input_key.startswith('uploads/'):
                logger.warning(f"Input key doesn't have 'uploads/' prefix: {input_key}, adding it")
                input_key = f"uploads/{input_key}"
                    
            if not output_key.startswith('processed/'):
                logger.warning(f"Output key doesn't have 'processed/' prefix: {output_key}, fixing it")
                output_key = f"processed/{user_id}/{output_filename}"
                logger.info(f"Updated output key to: {output_key}")
                    
            input_path = os.path.join('/tmp', input_filename)
            output_path = os.path.join('/tmp', output_filename)
            
            # Download input file
            logger.info(f"Downloading from s3://{bucket}/{input_key}")
            self.s3_client.download_file(bucket, input_key, input_path)
            logger.info(f"Downloaded input file: {input_path}")
            
            # Process video
            if self.process_video(input_path, output_path, effect_type):
                # Upload processed file with user metadata
                logger.info(f"Uploading to s3://{bucket}/{output_key}")
                
                self.s3_client.upload_file(
                    output_path, 
                    bucket, 
                    output_key,
                    ExtraArgs={
                        'ContentType': 'video/mp4',
                        'ContentDisposition': 'inline',
                        'Metadata': {
                            'user-id': user_id,
                            'effect-type': effect_type,
                            'created-at': datetime.now().isoformat(),
                            'original-filename': original_filename
                        }
                    }
                )
                logger.info(f"Uploaded processed file: {output_key}")
                
                # Delete the original uploaded video
                logger.info(f"Deleting original video from S3: {input_key}")
                self.s3_client.delete_object(
                    Bucket=bucket,
                    Key=input_key
                )
                logger.info(f"Successfully deleted original video: {input_key}")
                
                # Success
                return True
            else:
                logger.error("Video processing failed")
                return False
                    
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.error(traceback.format_exc())
            return False
        finally:
            # Clean up temporary files
            try:
                if 'input_path' in locals() and os.path.exists(input_path):
                    os.remove(input_path)
                if 'output_path' in locals() and os.path.exists(output_path):
                    os.remove(output_path)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary files: {str(e)}")
    
    def process_video(self, input_path, output_path, effect_type):
        """
        Process a video with the specified effect
        
        Args:
            input_path: Path to input video
            output_path: Path to output video
            effect_type: Type of effect to apply
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing video with effect: {effect_type}")
        
        # Special handling for Scanner Darkly effect - use direct class approach
        if effect_type.lower() in ["scanner-darkly", "scanner_darkly", "scannerdarkly"]:
            logger.info("Using direct class integration for Scanner Darkly effect")
            return process_scanner_darkly(input_path, output_path)
            
        # For other effects, use the registry
        if not self.registry:
            logger.error("Effect registry not initialized")
            return False
        
        try:
            # Sanitize paths to ensure input and output paths are different
            sanitized_input, sanitized_output = sanitize_paths(input_path, output_path)
            
            # If output path changed, log it
            if sanitized_output != output_path:
                logger.info(f"Using sanitized output path: {sanitized_output}")
            
            # Get the command for the effect
            command = self.registry.get_effect_command(effect_type, sanitized_input, sanitized_output)
            if not command:
                logger.error(f"Failed to get command for effect: {effect_type}")
                return False
            
            logger.info(f"Running FFmpeg command for effect: {effect_type}")
            logger.info(f"Command: {command}")
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg stderr: {result.stderr}")
                return False
            
            # If we used a different output path, rename it to the original requested path
            if sanitized_output != output_path:
                try:
                    logger.info(f"Renaming {sanitized_output} to {output_path}")
                    # Make sure the destination doesn't exist (should be the case)
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(sanitized_output, output_path)
                except Exception as rename_error:
                    logger.error(f"Error renaming output file: {str(rename_error)}")
                    # If rename fails, we can still continue since the file exists
            
            logger.info(f"Successfully processed video: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def download_core_module(self):
        """
        Download the effect_core.py module from S3
        
        Returns:
            Path to downloaded module or None if failed
        """
        try:
            core_key = f"{self.effects_prefix}core/effect_core.py"
            local_dir = "/tmp/video_effects_core"
            os.makedirs(local_dir, exist_ok=True)
            
            local_path = os.path.join(local_dir, "effect_core.py")
            logger.info(f"Downloading core module from s3://{self.bucket_name}/{core_key}")
            
            self.s3_client.download_file(self.bucket_name, core_key, local_path)
            os.chmod(local_path, 0o755)
            logger.info(f"Downloaded core module to {local_path}")
            
            return local_path
        except Exception as e:
            logger.error(f"Error downloading core module: {str(e)}")
            return None

# Main entry point for running as a service
def main():
    """
    Main entry point for the processor service
    """
    logger.info("Starting video processor service")
    
    # Get configuration from environment variables
    bucket_name = os.environ.get("BUCKET_NAME")
    queue_url = os.environ.get("QUEUE_URL")
    
    if not bucket_name or not queue_url:
        logger.error("Required environment variables not set:")
        logger.error(f"  BUCKET_NAME: {bucket_name}")
        logger.error(f"  QUEUE_URL: {queue_url}")
        return 1
        
    # Initialize processor
    processor = VideoProcessor(bucket_name=bucket_name)
    sqs_client = boto3.client('sqs', region_name='us-east-1')
    
    logger.info(f"Video processor initialized with:")
    logger.info(f"  Bucket: {bucket_name}")
    logger.info(f"  Queue: {queue_url}")
    
    # Main processing loop
    while True:
        try:
            logger.info("Polling for messages...")
            
            # Receive messages from SQS
            response = sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=600  # 10 minutes
            )
            
            # Process messages if any were received
            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        # Process the message
                        success = processor.process_message(message)
                        
                        # Delete the message if processing succeeded
                        if success:
                            sqs_client.delete_message(
                                QueueUrl=queue_url,
                                ReceiptHandle=message['ReceiptHandle']
                            )
                            logger.info("Message processed and deleted from queue")
                        else:
                            logger.warning("Processing failed, message will return to queue")
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        logger.error(traceback.format_exc())
            else:
                logger.info("No messages received")
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            logger.error(traceback.format_exc())
            # Sleep a bit before retrying to avoid tight polling on error
            import time
            time.sleep(5)
    
    return 0

# Entry point when run directly
if __name__ == "__main__":
    sys.exit(main())