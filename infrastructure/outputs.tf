output "cloudfront_domain" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "video_bucket_name" {
  value = aws_s3_bucket.video.id
}

output "sqs_queue_url" {
  value = aws_sqs_queue.video_processing.url
}

output "sqs_dlq_url" {
  value = aws_sqs_queue.video_processing_dlq.url
}