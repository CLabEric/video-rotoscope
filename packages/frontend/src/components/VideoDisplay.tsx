import React, { useState, useRef, useEffect } from 'react';
import { Download, Clock, AlertTriangle, RefreshCw } from 'lucide-react';
import { StorageNotice } from './StorageNotice';

interface VideoDisplayProps {
  type: 'original' | 'processed';
  videoUrl?: string;
  isProcessing?: boolean;
  effectType?: string;
  className?: string;
}

const VideoDisplay: React.FC<VideoDisplayProps> = ({
  type,
  videoUrl,
  isProcessing,
  effectType = 'silent-movie',
  className = ''
}) => {
  const title = type === 'original' ? 'Original Video' : 'Processed Video';
  const [videoError, setVideoError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // Reset error state when a new URL is provided
  useEffect(() => {
    if (videoUrl) {
      setVideoError(null);
    }
  }, [videoUrl]);

  const handleDownload = async () => {
    try {
      if (!videoUrl) return;
      
      const response = await fetch(videoUrl);
      if (!response.ok) {
        throw new Error(`Download failed with status: ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Use the effect type in the filename to help users identify different effects
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      a.download = `${effectType}-video-${timestamp}.mp4`;
      
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      setVideoError(error instanceof Error ? error.message : 'Download failed');
    }
  };

  // Handle video error
  const handleVideoError = () => {
    console.error('Video error occurred, URL:', videoUrl);
    setVideoError('Unable to play this video. The file may not be accessible.');
  };
  
  // Handle retry
  const handleRetry = () => {
    setVideoError(null);
    setRetryCount(prev => prev + 1);
    
    // Force video reload
    if (videoRef.current) {
      videoRef.current.load();
    }
  };

  // Determine processing text based on effect type
  const getProcessingText = () => {
    if (effectType === 'scanner-darkly') {
      return "Generating AI edge detection...";
    } else {
      return "Processing video...";
    }
  };

  // Get an estimate of processing time
  const getEstimatedTime = () => {
    if (effectType === 'scanner-darkly') {
      return "This may take 3-5 minutes";
    } else {
      return "This may take a minute";
    }
  };

  return (
    <div className={`flex flex-col bg-white rounded-xl overflow-hidden border border-orange-100 shadow-lg ${className}`}>
      <div className="bg-orange-50 p-2 border-b border-orange-100 flex justify-between items-center">
        <h3 className="text-sm font-semibold text-orange-900">{title}</h3>
        
        {type === 'processed' && isProcessing && (
          <div className="flex items-center gap-1 text-xs text-orange-600">
            <Clock className="w-3 h-3" />
            <span>Processing</span>
          </div>
        )}
      </div>
      
      {!videoUrl && type === 'original' ? (
        <div className="w-full aspect-video bg-gray-900 flex items-center justify-center">
          <p className="text-gray-400 text-sm text-center px-4">Original video will appear here</p>
        </div>
      ) : isProcessing && type === 'processed' ? (
        <div className="w-full aspect-video bg-gray-900 flex flex-col items-center justify-center space-y-3 p-4">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-orange-500" />
          <div className="text-center">
            <p className="text-gray-300 font-medium">{getProcessingText()}</p>
            <p className="text-gray-400 text-xs mt-2">{getEstimatedTime()}</p>
            {effectType === 'scanner-darkly' && (
              <div className="mt-3 bg-purple-900/30 px-3 py-2 rounded text-xs text-purple-200 max-w-xs">
                Using neural network edge detection for artistic effect
              </div>
            )}
          </div>
        </div>
      ) : videoUrl && !videoError ? (
        <div className="w-full flex flex-col">
          <video 
            ref={videoRef}
            src={`${videoUrl}${retryCount > 0 ? `&retry=${retryCount}` : ''}`}
            controls 
            className="w-full aspect-video object-contain bg-gray-900"
            onError={handleVideoError}
          />
          {type === 'processed' && (
            <div className="bg-orange-50 px-4 pt-4 pb-4">
              <StorageNotice />
              <div className="mt-4">
                <button
                  onClick={handleDownload}
                  className="w-full flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white py-3 px-4 rounded-lg transition-colors"
                >
                  <Download className="w-5 h-5" />
                  <span>Download Video</span>
                </button>
              </div>
            </div>
          )}
        </div>
      ) : videoError ? (
        <div className="w-full aspect-video bg-gray-900 flex flex-col items-center justify-center text-center p-4">
          <AlertTriangle className="w-10 h-10 text-orange-500 mb-3" />
          <p className="text-gray-300 max-w-sm">
            {videoError}
          </p>
          <button 
            onClick={handleRetry}
            className="mt-4 flex items-center gap-2 bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
      ) : (
        <div className="w-full aspect-video bg-gray-900 flex items-center justify-center">
          <p className="text-gray-400 text-sm text-center px-4">Video will appear here</p>
        </div>
      )}
    </div>
  );
};

export default VideoDisplay;