// src/config/aws.ts
export const awsConfig = {
  region: "us-east-1",
  credentials: {
    accessKeyId: process.env.NEXT_PUBLIC_AWS_ACCESS_KEY_ID || "",
    secretAccessKey: process.env.NEXT_PUBLIC_AWS_SECRET_ACCESS_KEY || "",
  },
  s3Bucket: process.env.NEXT_PUBLIC_S3_BUCKET_NAME || "",
  sqsQueueUrl: process.env.NEXT_PUBLIC_SQS_QUEUE_URL || "",
};
