import React from 'react';
import { Download } from 'lucide-react';
import { StorageNotice } from './StorageNotice';

interface VideoDisplayProps {
  type: 'original' | 'processed';
  videoUrl?: string;
  isProcessing?: boolean;
  className?: string;
}

const VideoDisplay: React.FC<VideoDisplayProps> = ({
  type,
  videoUrl,
  isProcessing,
  className = ''
}) => {
  const title = type === 'original' ? 'Original Video' : 'Processed Video';
  
  const handleDownload = async () => {
    try {
      const response = await fetch(videoUrl!);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `processed-video-${Date.now()}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

	// Complete return statement for VideoDisplay.tsx

	return (
	<div className={`flex flex-col bg-white rounded-xl overflow-hidden border border-orange-100 shadow-lg ${className}`}>
		<div className="bg-orange-50 p-2 border-b border-orange-100">
		<h3 className="text-sm font-semibold text-orange-900">{title}</h3>
		</div>
		
		{!videoUrl && type === 'original' ? (
		<div className="w-full aspect-video bg-gray-900 flex items-center justify-center">
			<p className="text-gray-400 text-sm text-center px-4">Original video will appear here</p>
		</div>
		) : isProcessing && type === 'processed' ? (
		<div className="w-full aspect-video bg-gray-900 flex flex-col items-center justify-center space-y-3">
			<div className="animate-spin rounded-full h-8 w-8 border-t-2 border-orange-500" />
			<p className="text-gray-400 text-sm text-center px-4">Processing video...</p>
		</div>
		) : videoUrl ? (
		<div className="w-full flex flex-col">
			<video 
			src={videoUrl} 
			controls 
			className="w-full aspect-video object-contain bg-gray-900"
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
		) : (
		<div className="w-full aspect-video bg-gray-900 flex items-center justify-center">
			<p className="text-gray-400 text-sm text-center px-4">Video will appear here</p>
		</div>
		)}
	</div>
	);
};

export default VideoDisplay;