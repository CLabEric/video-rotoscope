// app/api/video/[key]/route.ts
import { NextResponse } from "next/server";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

const s3Client = new S3Client({
  region: process.env.AWS_REGION || "us-east-1",
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || "",
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || "",
  },
});

export async function GET(
  request: Request,
  { params }: { params: { key: string } }
) {
  const headers = new Headers({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });

  try {
    // Get the params asynchronously
    const { key } = await params;

    if (!key) {
      return NextResponse.json(
        { error: "Key is required" },
        { status: 400, headers }
      );
    }

    const decodedKey = decodeURIComponent(key);

    const command = new GetObjectCommand({
      Bucket: process.env.S3_BUCKET_NAME,
      Key: decodedKey,
    });

    const signedUrl = await getSignedUrl(s3Client, command, {
      expiresIn: 3600,
      signableHeaders: new Set(["host"]),
    });

    return NextResponse.json({ url: signedUrl }, { headers });
  } catch (error) {
    console.error("Video URL error:", error);
    return NextResponse.json(
      { error: "Failed to generate video URL" },
      { status: 500, headers }
    );
  }
}
