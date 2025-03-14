// src/app/not-found.tsx
"use client";

import Link from "next/link";
import { ArrowLeft, Film, Video } from "lucide-react";
import { useEffect, useState } from "react";

export default function NotFound() {
  const [rotation, setRotation] = useState(0);
  
  // Create continuous rotation animation for the film icon
  useEffect(() => {
    const interval = setInterval(() => {
      setRotation(prev => (prev + 5) % 360);
    }, 100);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 bg-gradient-to-b from-white to-orange-50">
      <div className="max-w-md w-full text-center">
        <div className="relative mb-4 inline-block">
          <Film 
            className="w-32 h-32 text-orange-300" 
            style={{ transform: `rotate(${rotation}deg)` }}
          />
          <Video className="w-16 h-16 text-orange-500 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
        </div>
        
        <h1 className="text-9xl font-bold text-orange-500 tracking-tighter mb-3">
          404
        </h1>
        
        <h2 className="text-2xl font-semibold text-orange-900 mb-4">
          Scene Not Found
        </h2>
        
        <p className="text-orange-700 mb-8 max-w-sm mx-auto">
          Looks like the video you're looking for has been edited out of our final cut. 
          Let's get you back to the main timeline.
        </p>
        
        <Link 
          href="/"
          className="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-5 py-3 rounded-lg font-medium transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Homepage
        </Link>
      </div>
    </div>
  );
}