# output "cloudfront_domain" {
#   value = aws_cloudfront_distribution.frontend.domain_name
# }

# output "frontend_bucket" {
#   value = aws_s3_bucket.frontend.bucket
# }


# output "video_storage_bucket" {
#   value = aws_s3_bucket.video_storage.bucket
# }

# output "video_storage_bucket_arn" {
#   value = aws_s3_bucket.video_storage.arn
# }



# Outputs (outputs.tf)
output "frontend_cloudfront_domain" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "video_bucket_name" {
  value = aws_s3_bucket.video.id
}

output "sqs_queue_url" {
  value = aws_sqs_queue.video_processing.url
}