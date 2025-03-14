"use client"

import React from 'react';
import VideoUpload from '@/components/VideoUpload';
import Footer from '@/components/Footer';

export default function Dashboard() {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow container mx-auto py-8 px-4 max-w-6xl">
        <VideoUpload />
      </main>
      <Footer />
    </div>
  );
}