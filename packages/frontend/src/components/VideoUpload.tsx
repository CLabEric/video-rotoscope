"use client";
import React, { useState, useCallback, useEffect } from "react";
import { Upload, BrainCircuit } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { getUploadUrl, queueProcessing, checkProcessingStatus } from "@/lib/aws";
import EffectSelector from "./EffectSelector";
import Footer from "./Footer";
import VideoDisplay from "./VideoDisplay";

export default function VideoUpload() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [processedUrl, setProcessedUrl] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedEffect, setSelectedEffect] = useState("silent-movie");
  const [isProcessing, setIsProcessing] = useState(false);

	const handleUpload = async (file: File) => {
		try {
		// First set up the video preview
		const previewUrl = URL.createObjectURL(file);
		setPreview(previewUrl);
		setVideoFile(file);
		
		// Start the upload process
		setIsUploading(true);
		setUploadProgress(0);
		
		const { url, key } = await getUploadUrl(file.name, file.type);

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
			xhr.onload = () => xhr.status === 200 ? resolve(xhr.response) : reject();
			xhr.onerror = () => reject();
			xhr.send(file);
		});

		setIsProcessing(true);
		
		// Reset processed URL when starting new processing
		setProcessedUrl("");
		
		// Queue processing with selected effect
		await queueProcessing(key, selectedEffect);

		// Start polling for completion
		const checkStatus = async () => {
			try {
			const status = await checkProcessingStatus(key);
			console.log('Processing status:', status);
			
			if (status.status === "completed") {
				setProcessedUrl(status.key);
				setIsProcessing(false);
				return;
			}
			
			// Continue polling if not complete
			setTimeout(checkStatus, 2000);
			} catch (error) {
			console.error('Error checking status:', error);
			setTimeout(checkStatus, 2000);
			}
		};

		// Start the polling
		checkStatus();
		
		} catch (error) {
		console.error("Upload error:", error);
		setIsProcessing(false);
		} finally {
		setIsUploading(false);
		}
	};

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file?.type.startsWith("video/")) {
      handleUpload(file);
    }
  }, []);

  const handleEffectChange = (effectId: string) => {
    setSelectedEffect(effectId);
  };

  // Debug log to track state changes
  useEffect(() => {
    console.log("State updated:", { 
      isProcessing, 
      processedUrl, 
      hasVideoFile: !!videoFile 
    });
  }, [isProcessing, processedUrl, videoFile]);

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
      {/* Header */}
      <header className="w-full bg-transparent">
        <div className="container mx-auto max-w-6xl px-4 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h1 className="text-xl sm:text-2xl font-bold text-orange-900">Edge Detect Studio</h1>
            <div className="flex items-center gap-2 bg-orange-50 text-orange-800 px-2 py-1 sm:px-3 sm:py-2 rounded-lg">
              <BrainCircuit className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
              <span className="text-xs sm:text-sm">AI-Powered Video Effects</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center">
        <div className="container mx-auto max-w-6xl px-4 py-4 relative">
          {/* Video Processing View */}
          <div className={`w-full transition-all duration-500 ease-in-out ${videoFile ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none absolute inset-0'}`}>
            {videoFile && (
              <div className="pb-8">
				<div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:items-start">
				<div className="flex-shrink-0">
					<VideoDisplay type="original" videoUrl={preview} />
				</div>
				<div className="flex-shrink-0">
					<VideoDisplay type="processed" videoUrl={processedUrl} isProcessing={isProcessing} />
				</div>
				</div>

                <div className="h-[68px] mt-4">
                  {isUploading && (
                    <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-orange-100 p-3">
                      <div className="flex justify-between text-sm text-orange-800 mb-2">
                        <span>Uploading</span>
                        <span>{uploadProgress}%</span>
                      </div>
                      <Progress value={uploadProgress} className="h-2 bg-orange-200" />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Upload View */}
          <div className={`w-full max-w-lg mx-auto transition-all duration-500 ease-in-out ${!videoFile ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none absolute inset-0'}`}>
            <EffectSelector
              selectedEffect={selectedEffect}
              onEffectChange={handleEffectChange}
            />
            
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`
                mt-4 p-6 text-center border-4 border-dashed rounded-xl transition-all
                ${isDragging ? "border-orange-500 bg-orange-50" : "border-orange-200 hover:border-orange-500"}
              `}
            >
              <input
                type="file"
                accept="video/*"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleUpload(file);
                }}
                className="hidden"
                id="video-upload"
              />
              <label
                htmlFor="video-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <div className="bg-gradient-to-br from-orange-500 to-red-600 text-white rounded-full w-16 h-16 flex items-center justify-center mb-4">
                  <Upload className="w-8 h-8" />
                </div>
                <h2 className="text-xl font-bold text-orange-900 mb-2">
                  Upload Your Video
                </h2>
                <p className="text-orange-700 text-sm">
                  Drag and drop or click to select
                </p>
              </label>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}