// src/components/UserVideos.tsx
"use client";

import React, { useState, useEffect } from 'react';
import { useAuthContext } from '@/contexts/AuthContext';
import { listUserVideos } from '@/lib/aws';
import { Download, Film, RefreshCw, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';

interface UserVideo {
  key: string;
  url: string;
  timestamp: string;
  effectType: string;
  originalFilename?: string;
}

const UserVideos: React.FC = () => {
  const { userId } = useAuthContext();
  const [videos, setVideos] = useState<UserVideo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadVideos = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const userVideos = await listUserVideos(userId);
      setVideos(userVideos);
    } catch (error) {
      console.error('Error loading videos:', error);
      setError('Failed to load your videos. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (userId) {
      loadVideos();
    }
  }, [userId]);

  const handleDownload = async (video: UserVideo) => {
    try {
      const response = await fetch(video.url);
      if (!response.ok) {
        throw new Error(`Download failed with status: ${response.status}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Use original filename if available, otherwise create one
      const filename = video.originalFilename || 
        `${video.effectType}-video-${format(new Date(video.timestamp), 'yyyy-MM-dd-HHmm')}.mp4`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
      setError('Failed to download the video. Please try again.');
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM d, yyyy h:mm a');
    } catch (e) {
      return 'Unknown date';
    }
  };

  const getEffectName = (effectType: string) => {
    const effectMap: Record<string, string> = {
      'silent-movie': 'Silent Movie',
      'technicolor': 'Technicolor',
      'grindhouse': 'Grindhouse',
      'scanner-darkly': 'Scanner Darkly'
    };
    
    return effectMap[effectType] || effectType;
  };

  if (isLoading) {
    return (
      <div className="mt-12 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-orange-500 mb-4"></div>
        <p className="text-orange-700">Loading your videos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-8 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
        <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
        <div>
          <p className="text-red-700">{error}</p>
          <button 
            onClick={loadVideos} 
            className="mt-2 text-red-600 hover:text-red-800 text-sm flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Try Again
          </button>
        </div>
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <div className="mt-8 bg-orange-50 border border-orange-200 rounded-lg p-6 text-center">
        <Film className="w-12 h-12 text-orange-400 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-orange-900 mb-2">No Videos Yet</h3>
        <p className="text-orange-700 mb-4">
          You haven't processed any videos yet. Upload a video to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-orange-900">Your Videos</h2>
        <button
          onClick={loadVideos}
          className="text-orange-600 hover:text-orange-700 flex items-center gap-1 text-sm bg-orange-50 hover:bg-orange-100 px-3 py-1.5 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((video) => (
          <div key={video.key} className="bg-white rounded-lg overflow-hidden border border-orange-100 shadow-md">
            {/* Video Preview */}
            <div className="aspect-video bg-gray-900 relative">
              <video 
                src={video.url} 
                className="w-full h-full object-contain"
                controls
              />
            </div>
            
            {/* Video Info */}
            <div className="p-3">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    video.effectType === 'scanner-darkly' 
                      ? "bg-purple-100 text-purple-800"
                      : "bg-blue-100 text-blue-800"
                  }`}>
                    {getEffectName(video.effectType)}
                  </span>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDate(video.timestamp)}
                  </p>
                </div>
                <button
                  onClick={() => handleDownload(video)}
                  className="bg-orange-500 hover:bg-orange-600 text-white p-2 rounded-lg transition-colors"
                  title="Download Video"
                >
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-4 text-xs text-gray-500 bg-orange-50 rounded-lg p-3">
        <p>Note: Processed videos are automatically deleted after 24 hours. Download your videos to keep them.</p>
      </div>
    </div>
  );
};

export default UserVideos;