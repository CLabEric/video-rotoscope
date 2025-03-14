// packages/frontend/src/components/VideoUpload.tsx

"use client";
import React, { useState, useCallback, useEffect, useRef } from "react";
import { Upload, RefreshCw } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { getUploadUrl, queueProcessing, checkProcessingStatus } from "@/lib/aws";
import { useAuthContext } from "@/contexts/AuthContext";
import { listUserVideos } from "@/lib/aws";
import EffectSelector from "./EffectSelector";
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
  const [processingError, setProcessingError] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const { userId } = useAuthContext();

  const processingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const clearPreviousVideo = () => {
    // Clear any previous video states
    setProcessedUrl("");
    setIsProcessing(false);
    setProcessingError(null);
    setElapsedTime(0);
    
    // Clear timers
    if (processingTimerRef.current) {
      clearInterval(processingTimerRef.current);
      processingTimerRef.current = null;
    }
    
    if (pollingRef.current) {
      clearTimeout(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const handleUpload = async (file: File) => {
    try {
      clearPreviousVideo();
      
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

      await new Promise<void>((resolve, reject) => {
        xhr.open("PUT", url, true);
        xhr.setRequestHeader("Content-Type", file.type);
        xhr.onload = () => xhr.status === 200 ? resolve() : reject(new Error(`Upload failed with status ${xhr.status}`));
        xhr.onerror = () => reject(new Error("Upload failed"));
        xhr.send(file);
      });

      setIsProcessing(true);
      
      // Start processing timer
      processingTimerRef.current = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
      
      // Queue processing with selected effect - pass userId here
      await queueProcessing(key, selectedEffect, userId);

      // Start polling for completion
      const checkStatus = async () => {
        try {
          // First try the regular status check
          const status = await checkProcessingStatus(key, userId, selectedEffect);
          
          // If that doesn't work but we've waited at least 30 seconds, try finding it in the user's videos
          if (status.status !== "completed" && elapsedTime > 30) {
            console.log("Regular status check failed, trying to find video in user's videos");
            
            // Get the user's recent videos
            const userVideos = await listUserVideos(userId);
            
            // Look for videos uploaded in the last minute (likely our processed video)
            const recentVideo = userVideos.find(video => {
              const isRecent = (new Date().getTime() - new Date(video.timestamp).getTime()) < 60000;
              return isRecent;
            });
            
            if (recentVideo) {
              console.log("Found recent video:", recentVideo);
              setProcessedUrl(recentVideo.url);
              setIsProcessing(false);
              
              // Clear the processing timer
              if (processingTimerRef.current) {
                clearInterval(processingTimerRef.current);
                processingTimerRef.current = null;
              }
              return;
            }
          }
          
          // Continue with original logic
          if (status.status === "completed") {
            if (status.key) {
              setProcessedUrl(status.key);
            } else {
              setProcessingError("Processing completed but no URL was returned.");
            }
            setIsProcessing(false);
            
            // Clear the processing timer
            if (processingTimerRef.current) {
              clearInterval(processingTimerRef.current);
              processingTimerRef.current = null;
            }
            
            return;
          }
          
          // Continue polling if not complete
          pollingRef.current = setTimeout(checkStatus, 3000);
        } catch (error) {
          console.error('Error checking status:', error);
          // Don't stop polling on error, just try again
          pollingRef.current = setTimeout(checkStatus, 5000);
        }
      };

      // Start the polling
      checkStatus();
      
    } catch (error) {
      console.error("Upload error:", error);
      setProcessingError(error instanceof Error ? error.message : "An unknown error occurred");
      setIsProcessing(false);
      
      // Clear timers
      if (processingTimerRef.current) {
        clearInterval(processingTimerRef.current);
        processingTimerRef.current = null;
      }
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
    // Only allow changing effects when not processing
    if (!isProcessing && !isUploading) {
      setSelectedEffect(effectId);
    }
  };
  
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (processingTimerRef.current) {
        clearInterval(processingTimerRef.current);
      }
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
      }
    };
  }, []);

  // Reset video when changing effect
  const handleReset = () => {
    // Revoke object URLs to prevent memory leaks
    if (preview) URL.revokeObjectURL(preview);
    
    setVideoFile(null);
    setPreview("");
    setProcessedUrl("");
    clearPreviousVideo();
  };

  return (
    <div>
      {/* Video Processing View */}
      <div className={`w-full transition-all duration-500 ease-in-out ${videoFile ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none absolute inset-0'}`}>
        {videoFile && (
          <div>
            {/* Action Bar */}
            <div className="flex justify-between items-center mb-4">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 text-orange-600 hover:text-orange-700 bg-orange-50 hover:bg-orange-100 px-3 py-2 rounded-lg transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Another Video</span>
              </button>
              
              {isProcessing && (
                <div className="text-orange-600 flex items-center gap-2">
                  <span className="animate-pulse">Processing</span>
                  <span className="text-sm text-orange-500">{formatTime(elapsedTime)}</span>
                </div>
              )}
            </div>
            
            {/* Video Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:items-start">
              <div className="flex-shrink-0 order-1">
                <VideoDisplay 
                  type="original" 
                  videoUrl={preview} 
                />
              </div>
              <div className="flex-shrink-0 order-2">
                <VideoDisplay 
                  type="processed" 
                  videoUrl={processedUrl} 
                  isProcessing={isProcessing} 
                  effectType={selectedEffect}
                />
              </div>
            </div>

            {/* Progress and Errors */}
            <div className="mt-4 space-y-4">
              {isUploading && (
                <div className="bg-white rounded-xl shadow-lg overflow-hidden border border-orange-100 p-3">
                  <div className="flex justify-between text-sm text-orange-800 mb-2">
                    <span>Uploading</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2 bg-orange-200" />
                </div>
              )}
              
              {processingError && (
                <Alert variant="destructive" className="animate-appear">
                  <AlertTitle>Processing Failed</AlertTitle>
                  <AlertDescription>{processingError}</AlertDescription>
                </Alert>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Upload View */}
      <div className={`w-full transition-all duration-500 ease-in-out ${!videoFile ? 'scale-100 opacity-100' : 'scale-95 opacity-0 pointer-events-none absolute inset-0'}`}>
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
            mt-8 p-10 text-center border-4 border-dashed rounded-xl transition-all
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
            <p className="text-orange-700 text-sm max-w-md mx-auto">
              Drag and drop or click to select a video file. 
              For best results, use videos under 30 seconds.
            </p>
          </label>
        </div>
      </div>
    </div>
  );
}