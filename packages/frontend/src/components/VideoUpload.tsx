"use client";

import React, { useState, useCallback, useEffect } from "react";  // Add useEffect
import { Upload, BrainCircuit } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import {
  getUploadUrl,
  queueProcessing,
  checkProcessingStatus,
} from "@/lib/aws";
import EffectSelector from "./EffectSelector";
import Footer from "./Footer";

export default function VideoUpload() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [processedUrl, setProcessedUrl] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedEffect, setSelectedEffect] = useState("edge");
  const [processingStatus, setProcessingStatus] = useState<
    "uploading" | "processing" | "completed" | "failed"
  >("uploading");
  const [currentKey, setCurrentKey] = useState<string>("");  // Add this state

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

  useEffect(() => {
    const checkStatus = async () => {
      if (!currentKey) return;
      
      try {
        const result = await checkProcessingStatus(currentKey);
        console.log('Processing check result:', result);

        setProcessedUrl(result.key);
        if (result.status === "completed") {
          setProcessingStatus("completed");
        }
      } catch (error) {
        console.error('Error checking status:', error);
      }
    };

    let intervalId: NodeJS.Timeout;
    if (processingStatus === "processing") {
      intervalId = setInterval(checkStatus, 5000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [processingStatus, currentKey]);

  const handleUpload = async (file: File) => {
    try {
      setIsUploading(true);
      setUploadProgress(0);
      setProcessingStatus("uploading");

      const { url, key } = await getUploadUrl(file.name, file.type);
      setCurrentKey(key);  // Save the key

      const xhr = new XMLHttpRequest();

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percentComplete = (event.loaded / event.total) * 100;
          setUploadProgress(Math.round(percentComplete));
        }
      };

      await new Promise((resolve, reject) => {
        xhr.open("PUT", url, true);
        xhr.setRequestHeader("Content-Type", file.type);

        xhr.onload = () => {
          if (xhr.status === 200) {
            resolve(xhr.response);
          } else {
            reject(new Error("Upload failed"));
          }
        };

        xhr.onerror = () => reject(new Error("Upload failed"));
        xhr.send(file);
      });

      await queueProcessing(key);
      setProcessingStatus("processing");

    } catch (error) {
      console.error("Upload error:", error);
      setProcessingStatus("failed");
    } finally {
      setIsUploading(false);
    }
  };

  	const renderSwitch = (param: string) => {
		switch(param) {
			case 'processing':
				return (
					<div className="bg-orange-50 aspect-video flex flex-col items-center justify-center text-orange-700">
						<div className="animate-spin rounded-full h-12 w-12 sm:h-16 sm:w-16 border-t-2 border-orange-500 mb-2 sm:mb-4"></div>
						<p className="font-semibold text-sm sm:text-base">
							Applying AI edge detection. This may take a few minutes...
						</p>
					</div>
				);

			case 'completed':
				return (
					<>
						<video
							src={processedUrl}
							onError={(e) => console.log('Video error:', e)}
							controls
							className="w-full aspect-video object-contain bg-orange-50"
						/>
					</>
				);
			case 'failed':
				return (
					<div className="bg-orange-50 aspect-video flex items-center justify-center text-red-500 font-semibold text-sm sm:text-base">
						Processing Failed
					</div>
				);
			default:
				return (
					<div className="bg-orange-50 aspect-video flex items-center justify-center text-red-500 font-semibold text-sm sm:text-base">
						Processing...
					</div>
				);
		}
	}

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-orange-50 to-red-50 p-4 sm:p-8 font-['Libre_Baskerville'] flex flex-col">
      <div className="container mx-auto max-w-7xl flex-grow">
        {/* AI Powered Callout */}
        <div className="bg-orange-50 text-orange-800 p-3 text-center flex items-center gap-4 mb-6 rounded-xl">
          <div className="bg-orange-100 p-2 rounded-full flex items-center justify-center">
            <BrainCircuit className="w-6 h-6 text-orange-600" />
          </div>
          <div className="text-left flex-grow">
            <h2 className="text-base font-semibold">Powered by AI</h2>
            <p className="text-xs text-orange-700">
              Real-time video edge detection
            </p>
          </div>
        </div>

        {/* Header */}
        <header className="mb-8 sm:mb-12 px-4">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-orange-900 font-['Libre_Baskerville'] leading-tight text-center mx-auto max-w-full">
            Edge Detect Studio
          </h1>
          <p className="text-orange-800 text-sm sm:text-xl text-center mt-2 mx-auto max-w-[90%]">
            Transform your videos with real-time edge detection
          </p>
        </header>

        {/* Main Content Area */}
        <div className="space-y-8">
          {!videoFile ? (
            <>
              {/* Effect Selector */}
              <div className="w-full">
                <EffectSelector
                  selectedEffect={selectedEffect}
                  onEffectChange={setSelectedEffect}
                />
              </div>

              {/* Upload Area */}
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                className={`p-6 sm:p-12 text-center border-4 border-dashed rounded-3xl transition-all duration-300 w-full bg-white shadow-lg hover:shadow-xl ${
                  isDragging
                    ? "border-orange-500 bg-orange-50"
                    : "border-orange-200 hover:border-orange-500"
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
                  className="cursor-pointer flex flex-col items-center"
                >
                  <div className="bg-gradient-to-br from-orange-500 to-red-600 text-white rounded-full w-24 h-24 sm:w-32 sm:h-32 flex items-center justify-center mb-4 sm:mb-6 transform transition-transform hover:scale-110 shadow-xl hover:shadow-2xl">
                    <Upload className="w-12 h-12 sm:w-16 sm:h-16" />
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-bold text-orange-900 mb-2 text-center">
                    Upload Your Video
                  </h2>
                  <p className="text-orange-700 mb-4 text-sm sm:text-base text-center">
                    Drag and drop or click to select
                  </p>
                  <span className="px-4 py-2 sm:px-6 sm:py-3 bg-orange-50 text-orange-700 rounded-full font-semibold hover:bg-orange-100 transition-colors border border-orange-200 text-sm sm:text-base">
                    Choose File
                  </span>
                </label>
              </div>
            </>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
              {/* Original Video */}
              <div className="bg-white rounded-3xl overflow-hidden border border-orange-100 shadow-lg w-full">
                <div className="bg-orange-50 p-3 sm:p-4 border-b border-orange-100">
                  <h3 className="text-base sm:text-lg font-bold text-orange-900">
                    Original Video
                  </h3>
                </div>
                <video
                  src={preview}
                  controls
                  className="w-full aspect-video object-contain bg-orange-50"
                />
              </div>

              {/* Processed Video */}
              <div className="bg-white rounded-3xl overflow-hidden border border-orange-100 shadow-lg w-full">
                <div className="bg-orange-50 p-3 sm:p-4 border-b border-orange-100">
                  <h3 className="text-base sm:text-lg font-bold text-orange-900">
                    Processed Video
                  </h3>
                </div>
				{renderSwitch(processingStatus)}
              </div>
            </div>
          )}
        </div>

        {/* Upload Progress */}
        {isUploading && (
          <div className="mt-6 sm:mt-8 bg-white rounded-3xl shadow-lg overflow-hidden border border-orange-100">
            <div className="p-4 sm:p-6">
              <div className="flex justify-between text-xs sm:text-sm text-orange-800 mb-2">
                <span>Uploading</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress
                value={uploadProgress}
                className="h-2 sm:h-3 bg-orange-200"
              />
            </div>
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
