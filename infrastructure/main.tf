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

# Update the video bucket policy to reflect lifecycle rules
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
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.video.arn}/uploads/*"
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
      },
      {
        Sid       = "AllowInstanceAccessToEffects"
        Effect    = "Allow"
        Principal = {
          AWS = aws_iam_role.video_processor.arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.video.arn}/effects/*"
      }
    ]
  })
}

# Create a directory structure for effects in the video bucket
resource "aws_s3_object" "effects_core_dir" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/core/"
  content_type = "application/x-directory"
  source = "/dev/null"  # Empty content
}

resource "aws_s3_object" "effects_ffmpeg_dir" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/ffmpeg/"
  content_type = "application/x-directory"
  source = "/dev/null"  # Empty content
}

resource "aws_s3_object" "effects_neural_dir" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/neural/"
  content_type = "application/x-directory"
  source = "/dev/null"  # Empty content
}

# Upload the effect core module
resource "aws_s3_object" "effect_core_module" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/core/effect_core.py"
  source = "../packages/backend/src/effects/core/effect_core.py"
  etag   = filemd5("../packages/backend/src/effects/core/effect_core.py")
  content_type = "text/x-python"
}

# Upload the processor script
resource "aws_s3_object" "processor_script" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/processor.py"
  source = "../packages/backend/src/effects/processor.py"
  etag   = filemd5("../packages/backend/src/effects/processor.py")
  content_type = "text/x-python"
}

# Upload the effects manifest
resource "aws_s3_object" "effects_manifest" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/manifest.json"
  source = "../packages/backend/src/effects/manifest.json"
  etag   = filemd5("../packages/backend/src/effects/manifest.json")
  content_type = "application/json"
}

# Upload effect modules
resource "aws_s3_object" "silent_movie_effect" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/ffmpeg/silent_movie.py"
  source = "../packages/backend/src/effects/ffmpeg/silent_movie.py"
  etag   = filemd5("../packages/backend/src/effects/ffmpeg/silent_movie.py")
  content_type = "text/x-python"
}

resource "aws_s3_object" "grindhouse_effect" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/ffmpeg/grindhouse.py"
  source = "../packages/backend/src/effects/ffmpeg/grindhouse.py"
  etag   = filemd5("../packages/backend/src/effects/ffmpeg/grindhouse.py")
  content_type = "text/x-python"
}

resource "aws_s3_object" "technicolor_effect" {
  bucket = aws_s3_bucket.video.id
  key    = "effects/ffmpeg/technicolor.py"
  source = "../packages/backend/src/effects/ffmpeg/technicolor.py"
  etag   = filemd5("../packages/backend/src/effects/ffmpeg/technicolor.py")
  content_type = "text/x-python"
}

# Add the scanner-darkly effect module to S3
resource "aws_s3_object" "scanner_darkly_effect" {
  bucket        = aws_s3_bucket.video.id
  key           = "effects/neural/scanner_darkly.py"
  source        = "../packages/backend/src/effects/neural/scanner_darkly.py"
  etag          = filemd5("../packages/backend/src/effects/neural/scanner_darkly.py")
  content_type  = "text/x-python"
}

# Upload HED model files to S3
resource "aws_s3_object" "hed_model" {
  bucket        = aws_s3_bucket.video.id
  key           = "effects/neural/models/hed.caffemodel"
  source        = "../packages/backend/model_weights/hed.caffemodel"
  etag          = filemd5("../packages/backend/model_weights/hed.caffemodel")
  content_type  = "application/octet-stream"
}

resource "aws_s3_object" "hed_prototxt" {
  bucket        = aws_s3_bucket.video.id
  key           = "effects/neural/models/hed.prototxt"
  source        = "../packages/backend/model_weights/hed.prototxt"
  etag          = filemd5("../packages/backend/model_weights/hed.prototxt")
  content_type  = "text/plain"
}

# Create directory for models
resource "aws_s3_object" "effects_neural_models_dir" {
  bucket        = aws_s3_bucket.video.id
  key           = "effects/neural/models/"
  content_type  = "application/x-directory"
  source        = "/dev/null"  # Empty content
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
          "s3:DeleteObject",
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
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility",
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.video_processing.arn,
          aws_sqs_queue.video_processing_dlq.arn
        ]
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

# EC2 Spot Instance Configuration
resource "aws_spot_instance_request" "video_processor" {
  ami                   = "ami-09e2639b59ee94f7c"  # Deep Learning AMI GPU PyTorch 2.0.1
  instance_type         = "g4dn.xlarge"
  spot_price            = "0.20"  # Setting slightly above the current spot price
  spot_type             = "persistent"
  wait_for_fulfillment  = true
  instance_interruption_behavior = "stop"
  iam_instance_profile  = aws_iam_instance_profile.video_processor.name
  vpc_security_group_ids = [aws_security_group.video_processor.id]
  subnet_id             = "subnet-008674d77d1c4577c"
  associate_public_ip_address = true

  user_data = base64encode(templatefile("${path.module}/scripts/user-data.sh.tftpl", {
    queue_url    = aws_sqs_queue.video_processing.url
    bucket_name  = aws_s3_bucket.video.id
    dlq_url      = aws_sqs_queue.video_processing_dlq.url  # Add this line
  }))

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

# Add lifecycle configuration for video bucket
resource "aws_s3_bucket_lifecycle_configuration" "video_lifecycle" {
  bucket = aws_s3_bucket.video.id

  rule {
    id     = "delete_processed_videos"
    status = "Enabled"

    filter {
      prefix = "processed/"
    }

    # Delete processed videos after 24 hours
    expiration {
      days = 1
    }

    # Prevent accidental deletion during Terraform updates
    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }
}

# Dead Letter Queue for video processing
resource "aws_sqs_queue" "video_processing_dlq" {
  name = "${var.app_name}-video-processing-dlq"
  
  # DLQ retention period - keep failed messages for 14 days
  message_retention_seconds = 1209600
  
  # Encryption and other settings
  sqs_managed_sse_enabled = true
}

# Update the main queue with redrive policy
resource "aws_sqs_queue" "video_processing" {
  name = "${var.app_name}-video-processing"
  
  # Configure DLQ redrive policy - move messages to DLQ after 5 failed attempts
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.video_processing_dlq.arn
    maxReceiveCount     = 5
  })
  
  # Set visibility timeout to 10 minutes for long-running jobs
  visibility_timeout_seconds = 600
  
  # Add message attributes for tracking
  message_retention_seconds = 86400 # 1 day
  
  # Encryption
  sqs_managed_sse_enabled = true
}

# CloudWatch alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages_alarm" {
  alarm_name          = "${var.app_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This alarm monitors for messages in the DLQ"
  
  dimensions = {
    QueueName = aws_sqs_queue.video_processing_dlq.name
  }
}
