"use client";

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { queueProcessing } from '@/lib/aws';

export default function SuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const videoKey = searchParams.get('videoKey');
    const effectType = searchParams.get('effectType');
    const userId = searchParams.get('userId');
    
    if (videoKey && effectType && userId) {
      const startProcessing = async () => {
        try {
          await queueProcessing(videoKey, effectType, userId);
          // Wait a moment before redirecting
          setTimeout(() => {
            router.push('/dashboard?processing=true');
          }, 2000);
        } catch (err) {
          console.error('Error queueing video:', err);
          setError('Failed to start video processing');
          setIsProcessing(false);
        }
      };
      
      startProcessing();
    } else {
      setError('Missing required information');
      setIsProcessing(false);
    }
  }, []);
  
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl p-8 shadow-lg text-center">
        <h1 className="text-2xl font-bold text-green-600 mb-4">Payment Successful!</h1>
        
        {isProcessing && (
          <div>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <p className="text-orange-700">Starting your video processing...</p>
          </div>
        )}
        
        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-4">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}