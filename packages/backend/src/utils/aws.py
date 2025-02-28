#!/usr/bin/env python3
"""
AWS utilities for video processing
"""

import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, List, Optional, Union, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class AWSManager:
    """
    Manager for AWS services (S3, SQS)
    """
    def __init__(
        self,
        region: str = None,
        s3_bucket: str = None,
        sqs_queue_url: str = None
    ):
        """
        Initialize AWS manager
        
        Args:
            region: AWS region
            s3_bucket: S3 bucket name
            sqs_queue_url: SQS queue URL
        """
        # Get region from environment or parameter
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        
        # Get S3 bucket from environment or parameter
        self.s3_bucket = s3_bucket or os.environ.get("S3_BUCKET_NAME")
        
        # Get SQS queue URL from environment or parameter
        self.sqs_queue_url = sqs_queue_url or os.environ.get("SQS_QUEUE_URL")
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.sqs_client = boto3.client('sqs', region_name=self.region)
        
        # Validate configuration
        if not self.s3_bucket:
            logger.warning("S3 bucket not specified")
        
        if not self.sqs_queue_url:
            logger.warning("SQS queue URL not specified")
    
    def download_file(
        self, 
        s3_key: str, 
        local_path: str,
        bucket: str = None
    ) -> bool:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 object key
            local_path: Local path to save the file
            bucket: S3 bucket name (optional, uses default bucket if not specified)
            
        Returns:
            True if successful, False otherwise
        """
        bucket = bucket or self.s3_bucket
        if not bucket:
            logger.error("S3 bucket not specified")
            return False
        
        try:
            logger.info(f"Downloading s3://{bucket}/{s3_key} to {local_path}")
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download the file
            self.s3_client.download_file(bucket, s3_key, local_path)
            logger.info(f"Download complete: {local_path}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Error downloading file from S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading file: {str(e)}")
            return False
    
    def upload_file(
        self, 
        local_path: str, 
        s3_key: str,
        bucket: str = None,
        content_type: str = None,
        metadata: Dict[str, str] = None
    ) -> bool:
        """
        Upload a file to S3
        
        Args:
            local_path: Local path of the file
            s3_key: S3 object key
            bucket: S3 bucket name (optional, uses default bucket if not specified)
            content_type: Content type of the file
            metadata: Metadata to attach to the file
            
        Returns:
            True if successful, False otherwise
        """
        bucket = bucket or self.s3_bucket
        if not bucket:
            logger.error("S3 bucket not specified")
            return False
        
        try:
            logger.info(f"Uploading {local_path} to s3://{bucket}/{s3_key}")
            
            # Set up extra args
            extra_args = {}
            
            # Add content type if specified
            if content_type:
                extra_args['ContentType'] = content_type
            elif s3_key.endswith('.mp4'):
                extra_args['ContentType'] = 'video/mp4'
            
            # Add metadata if specified
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload the file
            self.s3_client.upload_file(
                local_path, 
                bucket, 
                s3_key, 
                ExtraArgs=extra_args
            )
            
            logger.info(f"Upload complete: s3://{bucket}/{s3_key}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {str(e)}")
            return False
    
    def receive_messages(
        self, 
        max_messages: int = 1,
        wait_time: int = 20,
        visibility_timeout: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Receive messages from SQS
        
        Args:
            max_messages: Maximum number of messages to receive
            wait_time: Wait time in seconds for long polling
            visibility_timeout: Visibility timeout in seconds
            
        Returns:
            List of messages
        """
        if not self.sqs_queue_url:
            logger.error("SQS queue URL not specified")
            return []
        
        try:
            logger.info(f"Receiving messages from {self.sqs_queue_url}")
            
            response = self.sqs_client.receive_message(
                QueueUrl=self.sqs_queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
                VisibilityTimeout=visibility_timeout,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
            )
            
            messages = response.get('Messages', [])
            
            if messages:
                logger.info(f"Received {len(messages)} messages")
                
                # Parse message bodies
                for message in messages:
                    try:
                        # Parse JSON body
                        message['ParsedBody'] = json.loads(message['Body'])
                    except:
                        logger.warning(f"Could not parse message body as JSON: {message['Body']}")
                        message['ParsedBody'] = None
            else:
                logger.info("No messages received")
            
            return messages
            
        except ClientError as e:
            logger.error(f"Error receiving messages from SQS: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error receiving messages: {str(e)}")
            return []
    
    def delete_message(self, receipt_handle: str) -> bool:
        """
        Delete a message from SQS
        
        Args:
            receipt_handle: Receipt handle of the message
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sqs_queue_url:
            logger.error("SQS queue URL not specified")
            return False
        
        try:
            logger.info(f"Deleting message {receipt_handle[:10]}... from {self.sqs_queue_url}")
            
            self.sqs_client.delete_message(
                QueueUrl=self.sqs_queue_url,
                ReceiptHandle=receipt_handle
            )
            
            logger.info("Message deleted")
            
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting message from SQS: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting message: {str(e)}")
            return False
    
    def extend_message_visibility(
        self, 
        receipt_handle: str, 
        visibility_timeout: int
    ) -> bool:
        """
        Extend the visibility timeout of a message
        
        Args:
            receipt_handle: Receipt handle of the message
            visibility_timeout: New visibility timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.sqs_queue_url:
            logger.error("SQS queue URL not specified")
            return False
        
        try:
            logger.info(f"Extending message visibility to {visibility_timeout} seconds")
            
            self.sqs_client.change_message_visibility(
                QueueUrl=self.sqs_queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=visibility_timeout
            )
            
            logger.info("Message visibility extended")
            
            return True
            
        except ClientError as e:
            logger.error(f"Error extending message visibility: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error extending visibility: {str(e)}")
            return False