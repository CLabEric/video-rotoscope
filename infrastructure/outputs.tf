output "cloudfront_domain" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}


output "video_storage_bucket" {
  value = aws_s3_bucket.video_storage.bucket
}

output "video_storage_bucket_arn" {
  value = aws_s3_bucket.video_storage.arn
}