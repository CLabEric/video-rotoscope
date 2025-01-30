import os
import boto3
import json
import sys
import logging
import logging.handlers
from botocore.exceptions import ClientError
import traceback
import subprocess
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s - %(filename)s:%(lineno)d'
)
logger = logging.getLogger(__name__)

# Initialize AWS clients
sqs = boto3.client('sqs')
s3 = boto3.client('s3')
queue_url = os.environ.get('QUEUE_URL')

def inspect_video(filepath, label="Video"):
    """Inspect video file and log details"""
    try:
        cmd = f'ffprobe -v error -show_format -show_streams -of json "{filepath}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            info = json.loads(result.stdout)
            logger.info(f"{label} Inspection:")
            logger.info(json.dumps(info, indent=2))
            return info
        else:
            logger.error(f"Failed to inspect {label.lower()}: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"Error inspecting {label.lower()}: {str(e)}")
        return None





def run_ffmpeg_command(command):
    """Run ffmpeg command and log output"""
    try:
        logger.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=True
        )
        logger.info(f"Command stdout: {result.stdout}")
        logger.info(f"Command stderr: {result.stderr}")
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg command failed: {result.stderr}")
        return result
    except Exception as e:
        logger.error(f"Failed to run command: {str(e)}")
        raise

def process_video(input_path, output_path):
    try:
        logger.info("*** RUNNING VERSION WITH MP4 CONTAINER ***")
        
        command = (
            f'ffmpeg -y -i "{input_path}" '
            f'-vf "format=gray,edgedetect=mode=colormix:high=0.9:low=0.1" '
            f'-c:v libx264 '
            f'-profile:v baseline '
            f'-preset medium '
            f'-pix_fmt yuv420p '
            f'-movflags +faststart '
            f'-f mp4 '  # Force MP4 format
            f'-map 0:v:0 '  # Only map video stream
            f'-an '  # No audio
            f'"{output_path}"'
        )
        
        logger.info(f"Running ffmpeg command: {command}")
        result = run_ffmpeg_command(command)
        logger.info(f"ffmpeg output: {result.stdout}")
        
        # Verify the container format
        verify_cmd = f'ffprobe -v error -show_format -show_streams "{output_path}"'
        verify_result = run_ffmpeg_command(verify_cmd)
        logger.info(f"Output format details: {verify_result.stdout}")

    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def process_message(message):
    try:
        body = json.loads(message['Body'])
        logger.info(f"Processing message: {json.dumps(body, indent=2)}")

        bucket = body['bucket']
        input_key = body['input_key']
        output_key = body['output_key']

        input_path = '/tmp/input.mp4'
        output_path = '/tmp/output.mp4'

        try:
            clean_key = input_key.replace(f"{bucket}/", "").lstrip("/")
            logger.info(f"Attempting download with cleaned key: {clean_key}")
            
            s3.head_object(Bucket=bucket, Key=clean_key)
            s3.download_file(bucket, clean_key, input_path)
            logger.info("Download successful!")
            
        except Exception as e:
            logger.error(f"S3 download failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

        process_video(input_path, output_path)

        try:
            logger.info(f"Uploading to S3: {bucket}/{output_key}")
            clean_output_key = output_key.replace(f"{bucket}/", "").lstrip("/")
            
            s3.upload_file(
                output_path, 
                bucket, 
                clean_output_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'ContentDisposition': 'inline'
                }
            )
            logger.info("Upload successful")
            
        except Exception as e:
            logger.error(f"S3 upload failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise

        os.remove(input_path)
        os.remove(output_path)
        logger.info("Message processed successfully")

    except Exception as e:
        logger.error(f"Message processing failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def check_health():
    try:
        pid = os.getpid()
        logger.info(f"Health check running, PID: {pid}")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False
    
def main():
    try:
        logger.info(f"Starting processor with queue URL: {queue_url}")
        logger.info("Container starting...")
        logger.info("Python version: %s", sys.version)
        logger.info("Current working directory: %s", os.getcwd())
        logger.info("Directory contents: %s", os.listdir())
        logger.info("Process ID: %s", os.getpid())
        logger.info("AWS Region: %s", os.environ.get('AWS_REGION'))
        
        # Test SQS connectivity
        try:
            queue_attrs = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=['ApproximateNumberOfMessages']
            )
            logger.info(f"Queue attributes: {queue_attrs}")
        except Exception as e:
            logger.error(f"Failed to get queue attributes: {e}")
        
        while True:
            check_health() 
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
                            process_message(message)
                            sqs.delete_message(
                                QueueUrl=queue_url,
                                ReceiptHandle=message['ReceiptHandle']
                            )
                        except Exception as e:
                            logger.error(f"Message processing error: {e}", exc_info=True)
                else:
                    logger.info("No messages received")

            except Exception as e:
                logger.error(f"Queue polling error: {e}", exc_info=True)
                
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()