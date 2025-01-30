"use client";

import React, { useState, useCallback, useEffect } from "react";
import {
  Upload,
  RefreshCcw,
  AlertCircle,
  CheckCircle2,
  Video,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";

export default function VideoUpload() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [processedUrl, setProcessedUrl] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<
    "uploading" | "processing" | "completed" | "failed"
  >("uploading");
  const [uploadedKey, setUploadedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!uploadedKey || processingStatus !== "processing") return;

    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/status?key=${uploadedKey}`);
        const data = await response.json();

        if (data.status === "completed") {
          setProcessingStatus("completed");
          try {
            const processedKey = `processed/${uploadedKey}`;
            const processedResponse = await fetch(
              `/api/video/${encodeURIComponent(processedKey)}`
            );

            if (!processedResponse.ok) {
              throw new Error("Failed to get video URL");
            }

            const responseData = await processedResponse.json();
            setProcessedUrl(responseData.url);
          } catch (error) {
            setProcessingStatus("failed");
          }
        }
      } catch (error) {
        setProcessingStatus("failed");
      }
    };

    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, [uploadedKey, processingStatus]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("video/")) {
      setVideoFile(file);
      setPreview(URL.createObjectURL(file));
      handleUpload(file);
    }
  }, []);

  const handleUpload = async (file: File) => {
    try {
      setIsUploading(true);
      setUploadProgress(0);

      const response = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          contentType: file.type,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to get upload URL");
      }

      const { url, key } = await response.json();

      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const progress = Math.round((event.loaded / event.total) * 100);
            setUploadProgress(progress);
          }
        });

        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(null);
          } else {
            reject(new Error("Upload failed"));
          }
        });

        xhr.addEventListener("error", () => reject(new Error("Upload failed")));

        xhr.open("PUT", url);
        xhr.send(file);
      });

      const processResponse = await fetch("/api/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key }),
      });

      if (!processResponse.ok) {
        throw new Error("Failed to queue processing");
      }

      await new Promise((resolve) => setTimeout(resolve, 500));

      setUploadedKey(key);
      setProcessingStatus("processing");
      setIsUploading(false);
    } catch (error) {
      setIsUploading(false);
      setProcessingStatus("failed");
    }
  };

  const handleReset = () => {
    setVideoFile(null);
    setPreview("");
    setProcessedUrl("");
    setUploadProgress(0);
    setUploadedKey(null);
    setProcessingStatus("uploading");
  };

  const getStatusMessage = () => {
    switch (processingStatus) {
      case "processing":
        return "Processing your video with edge detection...";
      case "completed":
        return "Processing complete! Check out your edge-detected video.";
      case "failed":
        return "Something went wrong. Please try again.";
      default:
        return "Transform your videos with real-time edge detection";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-indigo-50 to-purple-50 p-8">
      <div className="w-full max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center justify-center gap-3">
            <div className="p-2 bg-blue-500 rounded-lg">
              <Video className="w-8 h-8 text-white" />
            </div>
            Edge Detection Studio
          </h1>
          <p className="text-gray-600">
            Transform your videos with real-time edge detection
          </p>
        </div>

        {/* Status Alert */}
        <Alert className="mb-6 bg-white border-blue-100">
          <AlertCircle className="h-4 w-4 text-blue-500" />
          <AlertDescription className="text-gray-600">
            {getStatusMessage()}
          </AlertDescription>
        </Alert>

        {!videoFile ? (
          <Card className="border-none shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-gray-800">
                <Upload className="w-5 h-5 text-blue-500" />
                Upload Your Video
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-12 transition-all ${
                  isDragging
                    ? "border-blue-400 bg-blue-50"
                    : "border-gray-200 hover:border-blue-200 hover:bg-blue-50/50"
                }`}
              >
                <input
                  type="file"
                  accept="video/*"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setVideoFile(file);
                      setPreview(URL.createObjectURL(file));
                      handleUpload(file);
                    }
                  }}
                  className="hidden"
                  id="video-upload"
                />
                <label
                  htmlFor="video-upload"
                  className="flex flex-col items-center gap-6 cursor-pointer"
                >
                  <div className="p-6 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full shadow-lg">
                    <Upload className="w-10 h-10 text-white" />
                  </div>
                  <div className="text-center">
                    <p className="text-xl font-medium text-gray-700 mb-2">
                      Drop your video here or click to browse
                    </p>
                    <p className="text-sm text-gray-500">
                      MP4, WebM, and other video formats supported
                    </p>
                  </div>
                </label>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="border-none shadow-lg bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex justify-between items-center text-gray-800">
                <div className="flex items-center gap-2">
                  <CheckCircle2
                    className={`w-5 h-5 ${
                      processingStatus === "completed"
                        ? "text-green-500"
                        : "text-gray-400"
                    }`}
                  />
                  Video Processing
                </div>
                <button
                  onClick={handleReset}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                >
                  <RefreshCcw className="w-5 h-5 text-gray-600" />
                </button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-3">
                  <h3 className="font-medium text-gray-700 flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                    Original Video
                  </h3>
                  <div className="relative rounded-xl overflow-hidden bg-gray-900 aspect-video">
                    <video
                      src={preview}
                      controls
                      className="w-full h-full object-contain"
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="font-medium text-gray-700 flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                    Processed Video
                  </h3>
                  <div className="relative rounded-xl overflow-hidden bg-gray-900 aspect-video">
                    {processingStatus === "completed" && processedUrl ? (
                      <video
                        src={processedUrl}
                        controls
                        crossOrigin="anonymous"
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <div className="absolute inset-0 flex items-center justify-center bg-gray-900/90 backdrop-blur-sm">
                        <div className="text-center text-white">
                          {processingStatus === "processing" ? (
                            <div className="space-y-4">
                              <div className="relative">
                                <div className="w-12 h-12 border-4 border-blue-200/30 rounded-full animate-pulse"></div>
                                <div className="absolute top-0 left-0 w-12 h-12 border-4 border-blue-400 rounded-full animate-spin border-t-transparent"></div>
                              </div>
                              <p className="text-blue-100">
                                Processing your video...
                              </p>
                            </div>
                          ) : processingStatus === "failed" ? (
                            <div className="text-red-400">
                              Failed to process video
                            </div>
                          ) : (
                            "Waiting to start processing..."
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {isUploading && (
                <div className="mt-8 space-y-3">
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Uploading video...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
