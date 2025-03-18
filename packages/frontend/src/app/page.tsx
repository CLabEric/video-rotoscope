// Modify packages/frontend/src/app/page.tsx to use a single-page approach
"use client";
import React, { useState, useEffect } from 'react';
import VideoUpload from '@/components/VideoUpload';
import UserVideos from '@/components/UserVideos';
import Footer from '@/components/Footer';
import DashboardLoggedOut from '@/components/DashboardLoggedOut';
import { Upload, Film } from 'lucide-react';
import { useAuthContext } from '@/contexts/AuthContext';

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<string>("upload");
  const { user, loading } = useAuthContext();

  // Reset to upload tab when user logs in
  useEffect(() => {
    if (user) {
      setActiveTab("upload");
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <main className="flex-grow container mx-auto py-8 px-4 max-w-6xl flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <p className="text-orange-700">Loading...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Show logged out state if no user
  if (!user) {
    return (
      <div className="min-h-screen flex flex-col">
        <main className="flex-grow container mx-auto py-8 px-4 max-w-6xl">
          <DashboardLoggedOut />
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow container mx-auto py-8 px-4 max-w-6xl">
        {/* Simple Tabs */}
        <div className="mb-8">
          <div className="grid w-full max-w-md mx-auto grid-cols-2 bg-orange-50 rounded-lg overflow-hidden p-1">
            <button 
              onClick={() => setActiveTab("upload")}
              className={`flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${
                activeTab === "upload" 
                  ? "bg-white text-orange-900 shadow-sm" 
                  : "text-orange-700 hover:bg-orange-100"
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>Process Video</span>
            </button>
            <button 
              onClick={() => setActiveTab("videos")}
              className={`flex items-center justify-center gap-2 py-2 px-4 rounded-md transition-colors ${
                activeTab === "videos" 
                  ? "bg-white text-orange-900 shadow-sm" 
                  : "text-orange-700 hover:bg-orange-100"
              }`}
            >
              <Film className="w-4 h-4" />
              <span>My Videos</span>
            </button>
          </div>
        </div>
        
        {/* Tab Content */}
        <div>
          {activeTab === "upload" ? (
            <VideoUpload onProcessingComplete={() => setActiveTab("videos")} />
          ) : (
            <UserVideos />
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}