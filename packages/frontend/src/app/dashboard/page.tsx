"use client";

import React, { useState, useEffect } from 'react';
import VideoUpload from '@/components/VideoUpload';
import UserVideos from '@/components/UserVideos';
import { useAuthContext } from '@/contexts/AuthContext';
import { queueProcessing } from '@/lib/aws';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<string>("upload");
  const { user, userId, loading } = useAuthContext();
  const [processingStarted, setProcessingStarted] = useState(false);
  
  // Handle payment success
  useEffect(() => {
    // Check for payment success in URL hash
    if (typeof window !== 'undefined' && window.location.hash.startsWith('#payment-success')) {
      // Extract parameters
      const params = new URLSearchParams(window.location.hash.substring('#payment-success'.length));
      
      const videoKey = params.get('videoKey');
      const effectType = params.get('effectType');
      const paramUserId = params.get('userId');
      
      if (videoKey && effectType && paramUserId && paramUserId === userId) {
        // Process the video
        const startProcessing = async () => {
          try {
            await queueProcessing(videoKey, effectType, userId);
            setProcessingStarted(true);
            // Switch to videos tab
            setActiveTab("videos");
            // Clear the URL hash after processing
            window.history.replaceState(null, '', window.location.pathname);
          } catch (error) {
            console.error('Error processing video:', error);
            // You could show an error here
          }
        };
        
        startProcessing();
      }
    }
  }, [userId]); // Only run when userId is available
  
  // Rest of your dashboard component...
  
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow container mx-auto py-8 px-4 max-w-6xl">
        {/* Your tabs and content */}
        
        {/* Show processing message if needed */}
        {processingStarted && (
          <div className="mb-4 p-4 bg-green-50 text-green-700 rounded-lg">
            Payment successful! Your video is now being processed.
          </div>
        )}
        
        {/* Rest of your dashboard content */}
      </main>
    </div>
  );
}