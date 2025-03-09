// Path: packages/frontend/src/app/my-videos/page.tsx

'use client'

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { listUserVideos } from "@/lib/aws";

// Define ProcessedVideo interface
interface ProcessedVideo {
  key: string;
  filename: string;
  url: string;
  effectType: string;
  timestamp: Date;
}

export default function MyVideosPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [videos, setVideos] = useState<ProcessedVideo[]>([]); // Add type here
  const [loading, setLoading] = useState(true);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/");
    }
  }, [status, router]);
  
  // Load user's videos with proper type checking
  useEffect(() => {
    const fetchVideos = async () => {
      try {
        if (session?.user?.id) {
          // Only call this when we have a valid ID
          const userVideos = await listUserVideos(session.user.id);
          setVideos(userVideos);
        } else {
          // Handle case when ID is not available
          setVideos([]);
        }
      } catch (error) {
        console.error("Error fetching videos:", error);
      } finally {
        setLoading(false);
      }
    };
    
    // Only run fetchVideos when we're authenticated
    if (status === "authenticated") {
      fetchVideos();
    }
  }, [session, status]);
  
  if (status === "loading" || loading) {
    return <div>Loading...</div>;
  }
  
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-6">My Videos</h1>
      {videos.length === 0 ? (
        <p>You haven't processed any videos yet.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map(video => (
            <div key={video.key} className="border rounded p-4">
              <video src={video.url} controls className="w-full"></video>
              <p>{video.filename}</p>
              <p>Effect: {video.effectType}</p>
              <p>Created: {new Date(video.timestamp).toLocaleDateString()}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}