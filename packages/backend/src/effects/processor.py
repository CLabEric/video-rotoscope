#!/usr/bin/env python3
"""
Video processor for applying effects to uploaded videos
Uses dynamic effect loading from S3
"""

import os
import sys
import json
import logging
import boto3
import subprocess
import traceback
from botocore.exceptions import ClientError
import importlib.util
from typing import Dict, Any, Optional

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
        if not self.registry:
            logger.error("Effect registry not initialized")
            return False
        
        try:
            # Get the command for the effect
            command = self.registry.get_effect_command(effect_type, input_path, output_path)
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
            
            logger.info(f"Successfully processed video: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
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
            
            bucket = body.get('bucket')
            input_key = body.get('input_key')
            output_key = body.get('output_key')
            effect_type = body.get('effect_type', 'silent-movie')
            
            # Validate required fields
            if not bucket or not input_key or not output_key:
                logger.error(f"Message is missing required fields: {body}")
                return False
            
            # Create temporary file paths
            input_filename = os.path.basename(input_key)
            output_filename = os.path.basename(output_key)
            
            input_path = os.path.join('/tmp', input_filename)
            output_path = os.path.join('/tmp', output_filename)
            
            # Download input file
            logger.info(f"Downloading from s3://{bucket}/{input_key}")
            self.s3_client.download_file(bucket, input_key, input_path)
            logger.info(f"Downloaded input file: {input_path}")
            
            # Process video
            if self.process_video(input_path, output_path, effect_type):
                # Upload processed file
                logger.info(f"Uploading to s3://{bucket}/{output_key}")
                self.s3_client.upload_file(
                    output_path, 
                    bucket, 
                    output_key,
                    ExtraArgs={
                        'ContentType': 'video/mp4',
                        'ContentDisposition': 'inline'
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

def main():
    """
    Main entry point
    """
    logger.info("Video processor starting...")
    
    # Get environment variables
    bucket_name = os.environ.get('BUCKET_NAME')
    queue_url = os.environ.get('QUEUE_URL')
    
    # Validate environment variables
    if not bucket_name or not queue_url:
        logger.error("Required environment variables not set")
        logger.error(f"BUCKET_NAME: {bucket_name}")
        logger.error(f"QUEUE_URL: {queue_url}")
        sys.exit(1)
    
    # Initialize video processor
    processor = VideoProcessor(bucket_name=bucket_name)
    
    # Initialize SQS client
    sqs = boto3.client('sqs', region_name='us-east-1')
    
    logger.info(f"Using queue URL: {queue_url}")
    logger.info(f"Using bucket name: {bucket_name}")
    
    # Main processing loop
    while True:
        try:
            logger.info("Polling for messages...")
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )
            
            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        # Process the message
                        if processor.process_message(message):
                            # Delete the message if processing succeeded
                            sqs.delete_message(
                                QueueUrl=queue_url,
                                ReceiptHandle=message['ReceiptHandle']
                            )
                            logger.info("Deleted message from queue")
                        else:
                            logger.warning("Failed to process message, will retry later")
                    except Exception as e:
                        logger.error(f"Error handling message: {str(e)}")
                        logger.error(traceback.format_exc())
            else:
                logger.info("No messages received")
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()