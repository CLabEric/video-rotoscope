# Frontend S3 bucket and CloudFront
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.app_name}-frontend"
}

resource "aws_cloudfront_origin_access_identity" "frontend" {
  comment = "OAI for frontend bucket"
}

# Video S3 bucket and CloudFront OAI
resource "aws_s3_bucket" "video" {
  bucket = "${var.app_name}-video"
}

resource "aws_cloudfront_origin_access_identity" "video" {
  comment = "OAI for video bucket"
}

# S3 bucket policies
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
      }
      Action   = "s3:GetObject"
      Resource = "${aws_s3_bucket.frontend.arn}/*"
    }]
  })
}

# Add CORS configuration for the video bucket
resource "aws_s3_bucket_cors_configuration" "video" {
  bucket = aws_s3_bucket.video.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = ["*"]  # In production, restrict this to your domain
    expose_headers  = ["ETag", "Content-Type"]
    max_age_seconds = 3000
  }
}

# Update the video bucket policy to allow uploads
resource "aws_s3_bucket_policy" "video" {
  bucket = aws_s3_bucket.video.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontAccess"
        Effect    = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.video.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.video.arn}/*"
      },
      {
        Sid       = "AllowDirectUpload"
        Effect    = "Allow"
        Principal = "*"
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.video.arn}/uploads/*"
      },
      {
        Sid       = "CloudFrontReadAccess"
        Effect    = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.video.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.video.arn}/*"
      },
	  {
		Sid       = "AllowPublicReadForProcessedVideos"
		Effect    = "Allow"
		Principal = "*"
		Action    = "s3:GetObject"
		Resource  = "${aws_s3_bucket.video.arn}/processed/*"
	  }
    ]
  })
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled    = true
  default_root_object = "index.html"

  # Frontend origin
  origin {
    domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.frontend.bucket}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
    }
  }

  # Video bucket origin
  origin {
    domain_name = aws_s3_bucket.video.bucket_regional_domain_name
    origin_id   = "VideoS3Origin"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.video.cloudfront_access_identity_path
    }
  }

  # Default behavior (frontend)
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.bucket}"
    viewer_protocol_policy = "redirect-to-https"
    compress              = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  # Video files behavior
  ordered_cache_behavior {
    path_pattern           = "/processed/*"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "VideoS3Origin"
    viewer_protocol_policy = "redirect-to-https"
    compress              = true

    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# SQS Queue for video processing
resource "aws_sqs_queue" "video_processing" {
  name = "${var.app_name}-video-processing"
}

# Outputs
output "cloudfront_domain" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

# output "sqs_queue_url" {
#   value = aws_sqs_queue.video_processing.url
# }


# EC2 Spot Instance Configuration
resource "aws_iam_role" "video_processor" {
  name = "${var.app_name}-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "processor_policy" {
  name = "${var.app_name}-processor-policy"
  role = aws_iam_role.video_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.video.arn,
          "${aws_s3_bucket.video.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [aws_sqs_queue.video_processing.arn]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "video_processor" {
  name = "${var.app_name}-processor-profile"
  role = aws_iam_role.video_processor.name
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_spot_instance_request" "video_processor" {
  ami                    = "ami-0c104f6f4a5d9d1d5"  # Amazon Linux 2 AMI ID
  instance_type          = "t3.medium"
  spot_price            = "0.02"
  spot_type             = "persistent"
  wait_for_fulfillment  = true
  instance_interruption_behavior = "stop"
#   availability_zone = data.aws_availability_zones.available.names[0]
  iam_instance_profile = aws_iam_instance_profile.video_processor.name
  vpc_security_group_ids = [aws_security_group.video_processor.id]  # Change from security_groups

  # Add this block to specify the subnet
  subnet_id = "subnet-008674d77d1c4577c"  # Replace with your desired subnet ID

  # Add this block to assign a public IP
  associate_public_ip_address = true

user_data = base64encode(<<-EOF
    #!/bin/bash
    
    # Update system and install development tools
    yum update -y
    yum groupinstall -y "Development Tools"
    yum install -y autoconf automake bzip2 cmake freetype-devel gcc gcc-c++ git libtool make mercurial pkgconfig zlib-devel nasm python3-pip yasm

    # Create build directory
    cd /tmp
    mkdir -p ffmpeg_sources
    
    # Install x264 first
    cd ffmpeg_sources
    git clone --depth 1 https://code.videolan.org/videolan/x264.git
    cd x264
    ./configure --prefix="/usr/local" --enable-static --enable-shared
    make
    make install
    
    # Update library cache
    echo "/usr/local/lib" > /etc/ld.so.conf.d/local.conf
    ldconfig

    # Now install FFmpeg with x264 support
    cd /tmp/ffmpeg_sources
    wget https://ffmpeg.org/releases/ffmpeg-4.2.4.tar.bz2
    tar xjf ffmpeg-4.2.4.tar.bz2
    cd ffmpeg-4.2.4
    PKG_CONFIG_PATH="/usr/local/lib/pkgconfig" ./configure --prefix=/usr/local \
                --enable-gpl \
                --enable-nonfree \
                --enable-libx264 \
                --enable-shared \
                --extra-cflags="-I/usr/local/include" \
                --extra-ldflags="-L/usr/local/lib"
    make
    make install
    ldconfig

    # Verify library path
    echo "export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH" >> /etc/profile
    source /etc/profile

    # Install Python dependencies
    pip3 install boto3

    # Create processor directory
    mkdir -p /opt/video-processor
    cd /opt/video-processor

    # Create processor script
    cat > processor.py << 'PYTHON'
import os
import boto3
import json
import sys
import logging
import subprocess
import traceback
from botocore.exceptions import ClientError

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

def process_video(input_path, output_path):
    """Process video using FFmpeg with edge detection"""
    try:
        command = (
            f'ffmpeg -y -i "{input_path}" '
            f'-vf "format=gray,edgedetect=mode=colormix:high=0.9:low=0.1" '
            f'-c:v libx264 '
            f'-pix_fmt yuv420p '
            f'-f mp4 '
            f'"{output_path}"'
        )
        
        logger.info(f"Running FFmpeg command: {command}")
        
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        logger.info(f"FFmpeg stdout: {result.stdout}")
        logger.info(f"FFmpeg stderr: {result.stderr}")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg processing failed: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False

def main():
    logger.info("Video processor starting...")
    
    # Initialize AWS clients
    sqs = boto3.client('sqs')
    s3 = boto3.client('s3')
    
    queue_url = os.environ.get('QUEUE_URL')
    bucket_name = os.environ.get('BUCKET_NAME')
    
    logger.info(f"Using queue URL: {queue_url}")
    logger.info(f"Using bucket name: {bucket_name}")
    
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
                        body = json.loads(message['Body'])
                        logger.info(f"Processing message: {json.dumps(body, indent=2)}")
                        
                        bucket = body['bucket']
                        input_key = body['input_key']
                        output_key = body['output_key']
                        
                        # Create unique temp paths
                        input_path = f'/tmp/input_{os.path.basename(input_key)}'
                        output_path = f'/tmp/output_{os.path.basename(output_key)}'
                        
                        try:
                            # Download input file
                            logger.info(f"Downloading from s3://{bucket}/{input_key}")
                            s3.download_file(bucket, input_key, input_path)
                            logger.info(f"Downloaded input file: {input_path}")
                            
                            # Process video
                            if process_video(input_path, output_path):
                                # Upload processed file
                                logger.info(f"Uploading to s3://{bucket}/{output_key}")
                                s3.upload_file(
                                    output_path, 
                                    bucket, 
                                    output_key,
                                    ExtraArgs={
                                        'ContentType': 'video/mp4',
                                        'ContentDisposition': 'inline'
                                    }
                                )
                                logger.info(f"Uploaded processed file: {output_key}")
                                
                                # Delete message from queue
                                sqs.delete_message(
                                    QueueUrl=queue_url,
                                    ReceiptHandle=message['ReceiptHandle']
                                )
                                logger.info("Deleted message from queue")
                                
                            else:
                                logger.error("Video processing failed")
                                raise Exception("Video processing failed")
                                
                        except Exception as e:
                            logger.error(f"Processing error: {str(e)}")
                            raise
                            
                        finally:
                            # Cleanup temp files
                            if os.path.exists(input_path):
                                os.remove(input_path)
                            if os.path.exists(output_path):
                                os.remove(output_path)
                            
                    except Exception as process_error:
                        logger.error(f"Error processing message: {str(process_error)}")
                        logger.error(traceback.format_exc())
                        
            else:
                logger.info("No messages received")
                
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
PYTHON

    # Make processor script executable
    chmod +x processor.py

    # Create log file
    touch /var/log/video-processor.log
    chmod 666 /var/log/video-processor.log

    # Start processor
    export AWS_DEFAULT_REGION=us-east-1
    export QUEUE_URL=https://sqs.us-east-1.amazonaws.com/273354635152/video-rotoscope-video-processing
    export BUCKET_NAME=video-rotoscope-video
    cd /opt/video-processor
    export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
    nohup python3 processor.py >> /var/log/video-processor.log 2>&1 &
EOF
)

  tags = {
    Name = "${var.app_name}-processor"
  }
}

# Add security group for the instance
resource "aws_security_group" "video_processor" {
  name        = "${var.app_name}-processor-sg"
  description = "Security group for video processor"

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Add SSM policy to the instance role
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.video_processor.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# resource "aws_cloudfront_invalidation" "processed_videos" {
#   distribution_id = aws_cloudfront_distribution.frontend.id
#   paths           = ["/processed/*"]
# }

# # S3 bucket for frontend static files
# resource "aws_s3_bucket" "frontend" {
#   bucket = "${var.app_name}-frontend"
# }

# # Enable website hosting
# resource "aws_s3_bucket_website_configuration" "frontend" {
#   bucket = aws_s3_bucket.frontend.id

#   index_document {
#     suffix = "index.html"
#   }

#   error_document {
#     key = "index.html"
#   }
# }

# # CloudFront distribution
# resource "aws_cloudfront_distribution" "frontend" {
#   enabled             = true
#   is_ipv6_enabled    = true
#   default_root_object = "index.html"

#   origin {
#     domain_name = aws_s3_bucket.frontend.bucket_regional_domain_name
#     origin_id   = "S3-${aws_s3_bucket.frontend.bucket}"

#     s3_origin_config {
#       origin_access_identity = aws_cloudfront_origin_access_identity.frontend.cloudfront_access_identity_path
#     }
#   }

#   default_cache_behavior {
#     allowed_methods        = ["GET", "HEAD"]
#     cached_methods         = ["GET", "HEAD"]
#     target_origin_id       = "S3-${aws_s3_bucket.frontend.bucket}"
#     viewer_protocol_policy = "redirect-to-https"

#     forwarded_values {
#       query_string = false
#       cookies {
#         forward = "none"
#       }
#     }
#   }

#   restrictions {
#     geo_restriction {
#       restriction_type = "none"
#     }
#   }

#   viewer_certificate {
#     cloudfront_default_certificate = true
#   }
# }

# # CloudFront Origin Access Identity
# resource "aws_cloudfront_origin_access_identity" "frontend" {
#   comment = "OAI for ${var.app_name} frontend"
# }

# # S3 bucket policy for CloudFront access
# resource "aws_s3_bucket_policy" "frontend" {
#   bucket = aws_s3_bucket.frontend.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Principal = {
#           AWS = aws_cloudfront_origin_access_identity.frontend.iam_arn
#         }
#         Action   = "s3:GetObject"
#         Resource = "${aws_s3_bucket.frontend.arn}/*"
#       }
#     ]
#   })
# }


# # S3 bucket for video storage
# resource "aws_s3_bucket" "video_storage" {
#   bucket = "${var.app_name}-video-storage"
# }

# # Enable versioning for video storage
# resource "aws_s3_bucket_versioning" "video_storage" {
#   bucket = aws_s3_bucket.video_storage.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

# # CORS configuration for video storage
# resource "aws_s3_bucket_cors_configuration" "video_storage" {
#   bucket = aws_s3_bucket.video_storage.id

#   cors_rule {
#     allowed_headers = ["*"]
#     allowed_methods = ["GET", "HEAD", "PUT", "POST"]
#     allowed_origins = [
#       "http://localhost:3000",
#       "http://localhost:*",  # Add this
#       "https://*.amazonaws.com",
#       "https://*.cloudfront.net"
#     ]
#     expose_headers  = [
#       "ETag",
#       "x-amz-server-side-encryption",
#       "x-amz-request-id",
#       "x-amz-id-2",
#       "Content-Type",
#       "Content-Length"
#     ]
#     max_age_seconds = 3600
#   }
# }

# # Add lifecycle rules for video storage
# resource "aws_s3_bucket_lifecycle_configuration" "video_storage" {
#   bucket = aws_s3_bucket.video_storage.id

#   rule {
#     id     = "cleanup_unfinished_uploads"
#     status = "Enabled"

#     # Clean up incomplete multipart uploads after 7 days
#     abort_incomplete_multipart_upload {
#       days_after_initiation = 7
#     }
#   }

#   # New rule for processed videos
#   rule {
#     id     = "delete_processed_videos"
#     status = "Enabled"

#     filter {
#       prefix = "processed/"  # Only applies to processed videos
#     }

#     expiration {
#       days = 1  # Delete after 24 hours
#     }
#   }
# }

# # Add bucket policy for video storage
# resource "aws_s3_bucket_policy" "video_storage" {
#   bucket = aws_s3_bucket.video_storage.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Sid       = "PublicReadForProcessedVideos"
#         Effect    = "Allow"
#         Principal = "*"
#         Action    = "s3:GetObject"
#         Resource  = "${aws_s3_bucket.video_storage.arn}/processed/*"
#       }
#     ]
#   })
# }


# # Dead Letter Queue (DLQ) for failed processing attempts
# resource "aws_sqs_queue" "video_processing_dlq" {
#   name                      = "${var.app_name}-processing-dlq"
#   message_retention_seconds = 1209600 # 14 days
  
#   tags = {
#     Name = "${var.app_name}-dlq"
#   }
# }

# # Main processing queue
# resource "aws_sqs_queue" "video_processing" {
#   name                       = "${var.app_name}-processing-queue"
#   visibility_timeout_seconds = 900  # 15 minutes
#   message_retention_seconds  = 86400 # 1 day
#   delay_seconds             = 0
#   receive_wait_time_seconds = 20    # Enable long polling
  
#   # DLQ configuration
#   redrive_policy = jsonencode({
#     deadLetterTargetArn = aws_sqs_queue.video_processing_dlq.arn
#     maxReceiveCount     = 3  # Number of processing attempts before message goes to DLQ
#   })

#   # Enable server-side encryption
#   sqs_managed_sse_enabled = true
  
#   tags = {
#     Name = "${var.app_name}-queue"
#   }
# }


# # Add these to outputs.tf
# output "sqs_queue_url" {
#   value = aws_sqs_queue.video_processing.url
# }

# output "sqs_queue_arn" {
#   value = aws_sqs_queue.video_processing.arn
# }

# output "sqs_dlq_url" {
#   value = aws_sqs_queue.video_processing_dlq.url
# }

# output "sqs_dlq_arn" {
#   value = aws_sqs_queue.video_processing_dlq.arn
# }


# // ***** Add IAM roles and policies for queue access **** //


# # IAM role for video processing service
# resource "aws_iam_role" "video_processor" {
#   name = "${var.app_name}-processor-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Action = "sts:AssumeRole"
#         Effect = "Allow"
#         Principal = {
#           Service = "ecs-tasks.amazonaws.com"
#         }
#       }
#     ]
#   })
# }

# # Policy for accessing SQS queues
# # Remove the aws_iam_role_policy "sqs_full_access" block entirely
# # Update the sqs_access policy to include all permissions:

# resource "aws_iam_role_policy" "sqs_access" {
#   name = "${var.app_name}-sqs-access"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "sqs:SendMessage",
#           "sqs:ReceiveMessage",
#           "sqs:DeleteMessage",
#           "sqs:GetQueueAttributes",
#           "sqs:ChangeMessageVisibility",
#           "sqs:GetQueueUrl"
#         ]
#         Resource = [
#           aws_sqs_queue.video_processing.arn,
#           aws_sqs_queue.video_processing_dlq.arn
#         ]
#       }
#     ]
#   })
# }

# # Policy for accessing S3
# resource "aws_iam_role_policy" "s3_access" {
#   name = "${var.app_name}-s3-access"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "s3:GetObject",
#           "s3:PutObject",
#           "s3:DeleteObject",
#           "s3:ListBucket"
#         ]
#         Resource = [
#           aws_s3_bucket.video_storage.arn,
#           "${aws_s3_bucket.video_storage.arn}/*"
#         ]
#       }
#     ]
#   })
# }

# # CloudWatch logs policy
# resource "aws_iam_role_policy" "cloudwatch_logs" {
#   name = "${var.app_name}-cloudwatch-logs"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "logs:CreateLogGroup",
#           "logs:CreateLogStream",
#           "logs:PutLogEvents",
#           "logs:DescribeLogStreams"
#         ]
#         Resource = ["arn:aws:logs:*:*:*"]
#       }
#     ]
#   })
# }

# # Add to outputs.tf
# output "processor_role_arn" {
#   value = aws_iam_role.video_processor.arn
# }


# // ********** Set up the ECS service that will use these roles ********** //

# # ECR Repository for container images
# resource "aws_ecr_repository" "video_processor" {
#   name                 = "video-rotoscope-processor"  # Use the exact name that exists
#   image_tag_mutability = "MUTABLE"

#   image_scanning_configuration {
#     scan_on_push = true
#   }
# }

# # ECS Cluster
# resource "aws_ecs_cluster" "main" {
#   name = "${var.app_name}-cluster"
# }

# # CloudWatch Log Group
# resource "aws_cloudwatch_log_group" "video_processor" {
#   name              = "/ecs/${var.app_name}-processor"
#   retention_in_days = 30
# }

# # ECS Task Definition
# resource "aws_ecs_task_definition" "video_processor" {
#   family                   = "${var.app_name}-processor"
#   requires_compatibilities = ["FARGATE"]
#   network_mode			   = "awsvpc"
#   cpu   				   = "1024"  # 1 vCPU
#   memory 				   = "4096"  # 4GB (increased from 2GB)
#   execution_role_arn       = aws_iam_role.video_processor.arn
#   task_role_arn            = aws_iam_role.video_processor.arn

#   container_definitions = jsonencode([
#     {
#       name  = "video-processor"
#       image = "${aws_ecr_repository.video_processor.repository_url}:latest"
#       essential = true
#       environment = [
#         {
#           name  = "QUEUE_URL"
#           value = aws_sqs_queue.video_processing.url
#         },
#         {
#           name  = "BUCKET_NAME"
#           value = aws_s3_bucket.video_storage.id
#         },
#         {
#           name  = "AWS_DEFAULT_REGION"
#           value = var.aws_region
#         }
#       ]
#       logConfiguration = {
#         logDriver = "awslogs"
#         options = {
#           "awslogs-group"  = "/ecs/video-rotoscope-processor"
#           "awslogs-region" = var.aws_region
#           "awslogs-stream-prefix" = "ecs"
#         }
#       }
# 	  healthCheck = {
# 		command     = ["CMD-SHELL", "pidof python3 > /dev/stdout 2>/dev/stderr || exit 1"]
# 		interval    = 60
# 		timeout     = 10
# 		retries     = 3
# 		startPeriod = 120
# 	  }
      
#       # Increase memory/CPU if needed
# 	  memoryReservation = 2048
# 		cpu = 1024
# 		healthCheck = {
# 		command     = ["CMD-SHELL", "pgrep python || exit 1"]
# 		interval    = 60
# 		timeout     = 10
# 		retries     = 3
# 		startPeriod = 120
# 	  }
#       logConfiguration = {
#         logDriver = "awslogs"
#         options = {
#           "awslogs-group" = "/ecs/video-rotoscope-processor"
#           "awslogs-region" = var.aws_region
#           "awslogs-stream-prefix" = "ecs"
#           "awslogs-create-group" = "true"
#           "mode" = "non-blocking"
#         }
#       }
#     }
#   ])
#   skip_destroy = false
# }

# # Security Group for ECS Tasks
# resource "aws_security_group" "ecs_tasks" {
#   name        = "${var.app_name}-ecs-tasks"
#   description = "Allow outbound traffic from ECS tasks"
#   vpc_id      = aws_vpc.main.id

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }
# }

# # ECS Service
# resource "aws_ecs_service" "video_processor" {
#   force_new_deployment = true
#   name            = "${var.app_name}-processor"
#   cluster         = aws_ecs_cluster.main.id
#   task_definition = aws_ecs_task_definition.video_processor.arn
#   desired_count   = 1
#   launch_type     = "FARGATE"
#   deployment_minimum_healthy_percent = 100
#   deployment_maximum_percent = 200
#   enable_execute_command = true 
  
#   network_configuration {
#     subnets          = aws_subnet.private[*].id
#     security_groups  = [aws_security_group.ecs_tasks.id]
#     assign_public_ip = false
#   }
# }

# # Scale up policy
# resource "aws_appautoscaling_policy" "scale_up" {
#   name               = "${var.app_name}-scale-up"
#   policy_type        = "StepScaling"
#   resource_id        = aws_appautoscaling_target.ecs_target.resource_id
#   scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
#   service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

#   step_scaling_policy_configuration {
#     adjustment_type         = "ExactCapacity"
#     cooldown               = 60
#     metric_aggregation_type = "Maximum"

#     step_adjustment {
#       metric_interval_lower_bound = 0
#       scaling_adjustment         = 1
#     }
#   }
# }

# # Scale down policy
# resource "aws_appautoscaling_policy" "scale_down" {
#   name               = "${var.app_name}-scale-down"
#   policy_type        = "StepScaling"
#   resource_id        = aws_appautoscaling_target.ecs_target.resource_id
#   scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
#   service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

#   step_scaling_policy_configuration {
#     adjustment_type         = "ExactCapacity"
#     cooldown               = 60
#     metric_aggregation_type = "Maximum"

#     step_adjustment {
#       metric_interval_upper_bound = 0
#       scaling_adjustment         = 0
#     }
#   }
# }

# resource "aws_appautoscaling_target" "ecs_target" {
#   max_capacity       = 1
#   min_capacity       = 0
#   resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.video_processor.name}"
#   scalable_dimension = "ecs:service:DesiredCount"
#   service_namespace  = "ecs"
# }

# # Add to outputs.tf
# output "ecr_repository_url" {
#   value = aws_ecr_repository.video_processor.repository_url
# }

# output "ecs_cluster_name" {
#   value = aws_ecs_cluster.main.name
# }

# output "ecs_service_name" {
#   value = aws_ecs_service.video_processor.name
# }

# // ********** VPC Configuration ********** //
# # VPC
# resource "aws_vpc" "main" {
#   cidr_block           = "10.0.0.0/16"
#   enable_dns_hostnames = true
#   enable_dns_support   = true

#   tags = {
#     Name = "${var.app_name}-vpc"
#   }
# }

# # Public Subnets (2 for high availability)
# resource "aws_subnet" "public" {
#   count                   = 2
#   vpc_id                 = aws_vpc.main.id
#   cidr_block             = "10.0.${count.index + 1}.0/24"
#   availability_zone      = data.aws_availability_zones.available.names[count.index]
#   map_public_ip_on_launch = true

#   tags = {
#     Name = "${var.app_name}-public-${count.index + 1}"
#   }
# }

# # Private Subnets (2 for high availability)
# resource "aws_subnet" "private" {
#   count              = 2
#   vpc_id            = aws_vpc.main.id
#   cidr_block        = "10.0.${count.index + 10}.0/24"
#   availability_zone = data.aws_availability_zones.available.names[count.index]

#   tags = {
#     Name = "${var.app_name}-private-${count.index + 1}"
#   }
# }

# # Internet Gateway
# resource "aws_internet_gateway" "main" {
#   vpc_id = aws_vpc.main.id

#   tags = {
#     Name = "${var.app_name}-igw"
#   }
# }

# # Route Tables
# resource "aws_route_table" "public" {
#   vpc_id = aws_vpc.main.id

#   route {
#     cidr_block = "0.0.0.0/0"
#     gateway_id = aws_internet_gateway.main.id
#   }

#   tags = {
#     Name = "${var.app_name}-public-rt"
#   }
# }

# resource "aws_route_table" "private" {
#   vpc_id = aws_vpc.main.id

#   tags = {
#     Name = "${var.app_name}-private-rt"
#   }
# }

# # Route Table Associations
# resource "aws_route_table_association" "public" {
#   count          = 2
#   subnet_id      = aws_subnet.public[count.index].id
#   route_table_id = aws_route_table.public.id
# }

# resource "aws_route_table_association" "private" {
#   count          = 2
#   subnet_id      = aws_subnet.private[count.index].id
#   route_table_id = aws_route_table.private.id
# }

# # Data source for Availability Zones
# data "aws_availability_zones" "available" {
#   state = "available"
# }

# # Add to outputs.tf
# output "vpc_id" {
#   value = aws_vpc.main.id
# }

# output "public_subnet_ids" {
#   value = aws_subnet.public[*].id
# }

# output "private_subnet_ids" {
#   value = aws_subnet.private[*].id
# }

# // **********  VPC endpoints for AWS services ********** //
# # VPC Endpoint Security Group
# resource "aws_security_group" "vpc_endpoints" {
#   name        = "${var.app_name}-vpc-endpoints"
#   description = "Security group for VPC endpoints"
#   vpc_id      = aws_vpc.main.id

#   ingress {
#     from_port       = 443
#     to_port         = 443
#     protocol        = "tcp"
#     security_groups = [aws_security_group.ecs_tasks.id]
#   }

#   tags = {
#     Name = "${var.app_name}-vpc-endpoints-sg"
#   }
# }

# # S3 Gateway Endpoint
# resource "aws_vpc_endpoint" "s3" {
#   vpc_id            = aws_vpc.main.id
#   service_name      = "com.amazonaws.${var.aws_region}.s3"
#   vpc_endpoint_type = "Gateway"
  
#   route_table_ids = [
#     aws_route_table.private.id
#   ]

#   tags = {
#     Name = "${var.app_name}-s3-endpoint"
#   }
# }

# # SQS Interface Endpoint
# resource "aws_vpc_endpoint" "sqs" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.sqs"
#   vpc_endpoint_type   = "Interface"
#   private_dns_enabled = true
  
#   subnet_ids = aws_subnet.private[*].id
#   security_group_ids = [aws_security_group.vpc_endpoints.id]

#   tags = {
#     Name = "${var.app_name}-sqs-endpoint"
#   }
# }

# # ECR API Interface Endpoint
# resource "aws_vpc_endpoint" "ecr_api" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
#   vpc_endpoint_type   = "Interface"
#   private_dns_enabled = true
  
#   subnet_ids = aws_subnet.private[*].id
#   security_group_ids = [aws_security_group.vpc_endpoints.id]

#   tags = {
#     Name = "${var.app_name}-ecr-api-endpoint"
#   }
# }

# # ECR Docker Interface Endpoint
# resource "aws_vpc_endpoint" "ecr_dkr" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
#   vpc_endpoint_type   = "Interface"
#   private_dns_enabled = true
  
#   subnet_ids = aws_subnet.private[*].id
#   security_group_ids = [aws_security_group.vpc_endpoints.id]

#   tags = {
#     Name = "${var.app_name}-ecr-dkr-endpoint"
#   }
# }

# # CloudWatch Logs Interface Endpoint
# resource "aws_vpc_endpoint" "logs" {
#   vpc_id              = aws_vpc.main.id
#   service_name        = "com.amazonaws.${var.aws_region}.logs"
#   vpc_endpoint_type   = "Interface"
#   private_dns_enabled = true
  
#   subnet_ids = aws_subnet.private[*].id
#   security_group_ids = [aws_security_group.vpc_endpoints.id]

#   tags = {
#     Name = "${var.app_name}-logs-endpoint"
#   }
# }

# # Add these to outputs.tf
# output "vpc_endpoints" {
#   value = {
#     s3      = aws_vpc_endpoint.s3.id
#     sqs     = aws_vpc_endpoint.sqs.id
#     ecr_api = aws_vpc_endpoint.ecr_api.id
#     ecr_dkr = aws_vpc_endpoint.ecr_dkr.id
#     logs    = aws_vpc_endpoint.logs.id
#   }
# }


# // **********  additional security ********** //
# # Enable encryption for video storage bucket
# resource "aws_s3_bucket_server_side_encryption_configuration" "video_storage" {
#   bucket = aws_s3_bucket.video_storage.id

#   rule {
#     apply_server_side_encryption_by_default {
#       sse_algorithm = "AES256"
#     }
#   }
# }

# # Update the ECS tasks security group with more specific rules
# resource "aws_security_group_rule" "ecs_egress_https" {
#   type              = "egress"
#   from_port         = 443
#   to_port           = 443
#   protocol          = "tcp"
#   cidr_blocks       = ["0.0.0.0/0"]
#   security_group_id = aws_security_group.ecs_tasks.id
#   description       = "Allow HTTPS outbound traffic"
# }


# # add ECR permissions to the task execution role
# resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
#   role       = aws_iam_role.video_processor.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
# }

# resource "aws_iam_role_policy" "ecr_access" {
#   name = "${var.app_name}-ecr-access"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "ecr:GetAuthorizationToken",
#           "ecr:BatchCheckLayerAvailability",
#           "ecr:GetDownloadUrlForLayer",
#           "ecr:BatchGetImage"
#         ]
#         Resource = "*"
#       }
#     ]
#   })
# }
# resource "aws_iam_role_policy" "ecs_task_role_policy" {
#   name = "${var.app_name}-ecs-task-policy"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "s3:GetObject",
#           "s3:PutObject",
#           "s3:ListBucket"
#         ]
#         Resource = [
#           aws_s3_bucket.video_storage.arn,
#           "${aws_s3_bucket.video_storage.arn}/*"
#         ]
#       },
#       {
#         Effect = "Allow"
#         Action = [
#           "sqs:ReceiveMessage",
#           "sqs:DeleteMessage",
#           "sqs:GetQueueAttributes",
#           "sqs:GetQueueUrl"
#         ]
#         Resource = aws_sqs_queue.video_processing.arn
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy" "sqs_s3_access" {
#   name = "${var.app_name}-sqs-s3-access"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "sqs:ReceiveMessage",
#           "sqs:DeleteMessage",
#           "sqs:GetQueueAttributes"
#         ]
#         Resource = aws_sqs_queue.video_processing.arn
#       },
#       {
#         Effect = "Allow"
#         Action = [
#           "s3:GetObject",
#           "s3:PutObject"
#         ]
#         Resource = [
#           "${aws_s3_bucket.video_storage.arn}/*"
#         ]
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy" "sqs_send_message" {
#   name = "${var.app_name}-sqs-send-message"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "sqs:SendMessage",
#           "sqs:GetQueueUrl",
#           "sqs:GetQueueAttributes"
#         ]
#         Resource = aws_sqs_queue.video_processing.arn
#       }
#     ]
#   })
# }

# resource "aws_iam_role_policy" "ecs_exec" {
#   name = "${var.app_name}-ecs-exec"
#   role = aws_iam_role.video_processor.id

#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect = "Allow"
#       Action = [
#         "ssmmessages:CreateControlChannel",
#         "ssmmessages:CreateDataChannel",
#         "ssmmessages:OpenControlChannel",
#         "ssmmessages:OpenDataChannel"
#       ]
#       Resource = "*"
#     }]
#   })
# }

# # Scale up alarm
# resource "aws_cloudwatch_metric_alarm" "queue_not_empty" {
#   alarm_name          = "${var.app_name}-queue-not-empty"
#   comparison_operator = "GreaterThanOrEqualToThreshold"
#   evaluation_periods  = "1"
#   metric_name         = "ApproximateNumberOfMessagesVisible"
#   namespace           = "AWS/SQS"
#   period              = "60"
#   statistic          = "Average"
#   threshold          = "1"
#   alarm_description   = "Scale up when there are messages in the queue"
#   alarm_actions      = [aws_appautoscaling_policy.scale_up.arn]  # This uses the correct ARN reference

#   dimensions = {
#     QueueName = aws_sqs_queue.video_processing.name
#   }
# }

# # Scale down alarm
# resource "aws_cloudwatch_metric_alarm" "queue_empty" {
#   alarm_name          = "${var.app_name}-queue-empty"
#   comparison_operator = "LessThanOrEqualToThreshold"
#   evaluation_periods  = "2"
#   metric_name         = "ApproximateNumberOfMessagesVisible"
#   namespace           = "AWS/SQS"
#   period              = "300"
#   statistic           = "Maximum"
#   threshold           = "0"
#   alarm_description   = "Scale down when queue is empty"
#   alarm_actions       = [aws_appautoscaling_policy.scale_down.arn]

#   dimensions = {
#     QueueName = aws_sqs_queue.video_processing.name
#   }
# }

# # AWS Budget for monthly cost tracking
# resource "aws_budgets_budget" "monthly" {
#   name              = "monthly-budget"
#   budget_type       = "COST"
#   limit_amount      = "10"  # Set your desired limit - $10 for example
#   limit_unit        = "USD"
#   time_period_start = "2024-01-01_00:00"
#   time_unit         = "MONTHLY"

#   notification {
#     comparison_operator        = "GREATER_THAN"
#     threshold                  = 80
#     threshold_type            = "PERCENTAGE"
#     notification_type         = "ACTUAL"
#     subscriber_email_addresses = ["your-email@example.com"]  # Replace with your email
#   }

#   notification {
#     comparison_operator        = "GREATER_THAN"
#     threshold                  = 100
#     threshold_type            = "PERCENTAGE"
#     notification_type         = "ACTUAL"
#     subscriber_email_addresses = ["your-email@example.com"]  # Replace with your email
#   }

#   # Alert for forecasted spend
#   notification {
#     comparison_operator        = "GREATER_THAN"
#     threshold                  = 100
#     threshold_type            = "PERCENTAGE"
#     notification_type         = "FORECASTED"
#     subscriber_email_addresses = ["your-email@example.com"]  # Replace with your email
#   }
# }