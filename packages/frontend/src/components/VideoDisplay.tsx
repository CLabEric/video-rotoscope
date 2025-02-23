import React from 'react';
import { Download } from 'lucide-react';

interface VideoDisplayProps {
  type: 'original' | 'processed';
  videoUrl?: string;
  isProcessing?: boolean;
  onDownload?: () => void;
  className?: string;
}

const VideoDisplay: React.FC<VideoDisplayProps> = ({
  type,
  videoUrl,
  isProcessing,
  onDownload,
  className = ''
}) => {
  const title = type === 'original' ? 'Original Video' : 'Processed Video';
  
  const renderContent = () => {
    if (!videoUrl && type === 'original') {
      return (
        <div className="w-full h-full bg-gray-900 flex items-center justify-center">
          <p className="text-gray-400 text-sm text-center px-4">Original video will appear here</p>
        </div>
      );
    }

    if (isProcessing && type === 'processed') {
      return (
        <div className="w-full h-full bg-gray-900 flex flex-col items-center justify-center space-y-3">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-orange-500" />
          <p className="text-gray-400 text-sm text-center px-4">Processing video...</p>
        </div>
      );
    }

    return (
      <div className="relative w-full h-full">
        <video 
          src={videoUrl} 
          controls 
          className="absolute inset-0 w-full h-full object-contain bg-gray-900"
        />
        {type === 'processed' && onDownload && (
          <button
            onClick={onDownload}
            className="absolute bottom-4 right-4 bg-orange-500 hover:bg-orange-600 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            title="Download processed video"
          >
            <Download className="w-5 h-5" />
          </button>
        )}
      </div>
    );
  };

  return (
    <div className={`flex flex-col bg-white rounded-xl overflow-hidden border border-orange-100 shadow-lg ${className}`}>
      <div className="bg-orange-50 p-2 border-b border-orange-100">
        <h3 className="text-sm font-semibold text-orange-900">{title}</h3>
      </div>
      <div className="relative w-full pt-[56.25%]">
        <div className="absolute inset-0">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default VideoDisplay;