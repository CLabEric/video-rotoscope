import os
import boto3
import json
import sys
import logging
from botocore.exceptions import ClientError
import subprocess
import traceback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/video-processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

def process_video(input_path, output_path):
    try:
        command = (
            f'ffmpeg -y -i "{input_path}" '
            f'-vf "format=gray,edgedetect=mode=colormix:high=0.9:low=0.1" '
            f'-c:v libx264 -preset medium -pix_fmt yuv420p '
            f'-movflags +faststart -f mp4 "{output_path}"'
        )
        
        logger.info(f"Running ffmpeg command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
            
        logger.info("Video processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise

def main():
    logger.info("Video processor starting...")
    sqs = boto3.client('sqs')
    s3 = boto3.client('s3')
    queue_url = os.environ['QUEUE_URL']
    
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
                        logger.info(f"Processing message: {message['MessageId']}")
                        body = json.loads(message['Body'])
                        
                        # Download input video
                        input_path = '/tmp/input.mp4'
                        output_path = '/tmp/output.mp4'
                        s3.download_file(body['bucket'], body['input_key'], input_path)
                        logger.info("Downloaded input video")
                        
                        # Process video
                        process_video(input_path, output_path)
                        
                        # Upload result
                        s3.upload_file(
                            output_path, 
                            body['bucket'], 
                            body['output_key'],
                            ExtraArgs={'ContentType': 'video/mp4'}
                        )
                        logger.info("Uploaded processed video")
                        
                        # Clean up
                        os.remove(input_path)
                        os.remove(output_path)
                        
                        # Delete message
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        logger.info("Processing completed successfully")
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        logger.error(traceback.format_exc())
            else:
                logger.info("No messages received")
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()