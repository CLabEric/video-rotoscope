// Path: packages/frontend/src/app/dashboard/page.tsx

"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { listUserVideos } from "@/lib/aws";
import { Upload, Clock, Film } from "lucide-react";
import VideoUpload from "@/components/VideoUpload";
import Footer from "@/components/Footer";

// Define the ProcessedVideo interface
interface ProcessedVideo {
  key: string;
  filename: string;
  url: string;
  effectType: string;
  timestamp: Date;
}

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [videos, setVideos] = useState<ProcessedVideo[]>([]); // Add type here
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/");
    }
  }, [status, router]);
  
	// Fix the useEffect section with proper type handling:
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
  
  // Loading state
  if (status === "loading" || (status === "authenticated" && loading)) {
    return (
      <div className="min-h-screen flex flex-col bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-orange-800">Loading your videos...</p>
          </div>
        </div>
      </div>
    );
  }
  
  // Dashboard content
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
      <main className="flex-1 container mx-auto max-w-6xl px-4 py-8">
        {/* Dashboard Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-orange-900">Your Dashboard</h1>
            <p className="text-orange-700">
              Welcome back, {session?.user?.name?.split(' ')?.[0] || 'User'}
            </p>
          </div>
          
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-6 rounded-lg flex items-center gap-2 shadow-md transition-colors self-start"
          >
            <Upload size={18} />
            {showUpload ? "Hide Upload" : "Create New Video"}
          </button>
        </div>
        
        {/* Upload Area (Collapsible) */}
        {showUpload && (
          <div className="mb-12 bg-white rounded-xl p-6 shadow-md">
            <VideoUpload />
          </div>
        )}
        
        {/* Recent Videos */}
        <div className="mb-8">
          <h2 className="text-2xl font-semibold text-orange-900 mb-4">Recent Videos</h2>
          
          {videos.length === 0 ? (
            <div className="bg-white rounded-xl p-8 text-center">
              <div className="flex justify-center mb-4">
                <Film size={48} className="text-orange-300" />
              </div>
              <h3 className="text-xl font-medium text-orange-900 mb-2">No videos yet</h3>
              <p className="text-orange-700 mb-6">
                Upload your first video to see the magic happen!
              </p>
              <button
                onClick={() => setShowUpload(true)}
                className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-2 px-4 rounded-lg inline-flex items-center gap-2"
              >
                <Upload size={16} />
                Upload Video
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videos.map((video) => (
                <div key={video.key} className="bg-white rounded-xl overflow-hidden shadow-md">
                  <div className="aspect-video bg-gray-900 relative">
                    <video 
                      src={video.url} 
                      className="w-full h-full object-contain"
                      controls
                    />
                  </div>
                  <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium text-orange-900 truncate pr-2">
                        {video.filename.substring(video.filename.indexOf('_') + 1)}
                      </h3>
                      <span className="text-xs bg-orange-100 text-orange-800 px-2 py-1 rounded-full">
                        {video.effectType}
                      </span>
                    </div>
                    <div className="flex items-center text-xs text-gray-500">
                      <Clock size={12} className="mr-1" />
                      {new Date(video.timestamp).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
      
      <Footer />
    </div>
  );
}