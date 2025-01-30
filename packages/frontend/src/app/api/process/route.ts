// app/api/process/route.ts
import { NextResponse } from "next/server";
import { SQSClient, SendMessageCommand } from "@aws-sdk/client-sqs";

const sqsClient = new SQSClient({
  region: process.env.AWS_REGION || "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || "",
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "",
  },
});

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { key } = body;

    if (!key) {
      return NextResponse.json(
        { error: "Video key is required" },
        { status: 400 }
      );
    }

    const message = {
      bucket: process.env.S3_BUCKET_NAME,
      input_key: key,
      output_key: `processed/${key}`,
    };

    const command = new SendMessageCommand({
      QueueUrl: process.env.SQS_QUEUE_URL,
      MessageBody: JSON.stringify(message),
    });

    await sqsClient.send(command);

    return NextResponse.json({ status: "queued", key });
  } catch (error) {
    console.error("Processing error:", error);
    return NextResponse.json(
      { error: "Failed to queue processing" },
      { status: 500 }
    );
  }
}
