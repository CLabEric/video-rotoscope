"use client"

import React, { useState } from 'react';
import VideoUpload from '@/components/VideoUpload';
import UserVideos from '@/components/UserVideos';
import Footer from '@/components/Footer';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, Film } from 'lucide-react';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<string>("upload");

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow container mx-auto py-8 px-4 max-w-6xl">
        <Tabs defaultValue="upload" value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full max-w-md mx-auto grid-cols-2 mb-8">
            <TabsTrigger value="upload" className="flex gap-2 items-center">
              <Upload className="w-4 h-4" />
              <span>Process Video</span>
            </TabsTrigger>
            <TabsTrigger value="videos" className="flex gap-2 items-center">
              <Film className="w-4 h-4" />
              <span>My Videos</span>
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="upload">
            <VideoUpload onProcessingComplete={() => setActiveTab("videos")} />
          </TabsContent>
          
          <TabsContent value="videos">
            <UserVideos />
          </TabsContent>
        </Tabs>
      </main>
      <Footer />
    </div>
  );
}