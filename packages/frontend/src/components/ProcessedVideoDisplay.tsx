import { Download, AlertCircle } from 'lucide-react';

interface ProcessedVideoDisplayProps {
  videoUrl: string;
  processingStatus: 'processing' | 'completed' | 'failed';
}

const ProcessedVideoDisplay = ({ videoUrl, processingStatus }: ProcessedVideoDisplayProps) => {
  const handleDownload = async () => {
    try {
      const response = await fetch(videoUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'processed-video.mp4';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const StorageNotice = () => (
    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-start gap-3">
      <AlertCircle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
      <div>
        <h4 className="text-sm font-semibold text-orange-900 mb-1">
          Temporary Storage Notice
        </h4>
        <p className="text-sm text-orange-700">
          Please note that processed videos are automatically deleted after 24 hours. 
          Make sure to download your video if you want to keep it.
        </p>
      </div>
    </div>
  );

  const renderContent = () => {
    switch(processingStatus) {
      case 'processing':
        return (
          <div className="aspect-video flex flex-col items-center justify-center text-orange-700 bg-gray-900">
            <div className="animate-spin rounded-full h-12 w-12 sm:h-16 sm:w-16 border-t-2 border-orange-500 mb-2 sm:mb-4"></div>
            <p className="font-semibold text-sm sm:text-base">
              Applying AI edge detection. This may take a few minutes...
            </p>
          </div>
        );

      case 'completed':
        return (
          <div>
            <video
              src={videoUrl}
              controls
              className="w-full aspect-video object-contain bg-gray-900"
            />
            <div className="pt-4 px-4">
              <StorageNotice />
              <button
                onClick={handleDownload}
                className="w-full flex items-center justify-center gap-2 bg-orange-500 hover:bg-orange-600 text-white py-3 px-4 rounded-lg transition-colors mt-4"
              >
                <Download className="w-5 h-5" />
                <span>Download Video</span>
              </button>
            </div>
          </div>
        );

      case 'failed':
        return (
          <div className="aspect-video flex items-center justify-center text-red-500 font-semibold text-sm sm:text-base bg-gray-900">
            Processing Failed
          </div>
        );

      default:
        return (
          <div className="aspect-video flex items-center justify-center text-orange-500 font-semibold text-sm sm:text-base bg-gray-900">
            Processing...
          </div>
        );
    }
  };

  return (
    <div className="bg-white rounded-3xl overflow-hidden border border-orange-100 shadow-lg w-full">
      <div className="bg-orange-50 p-3 sm:p-4 border-b border-orange-100">
        <h3 className="text-base sm:text-lg font-bold text-orange-900">
          Processed Video
        </h3>
      </div>
      {/* Keep consistent padding only for the title, not for the content */}
      <div>
        {renderContent()}
      </div>
    </div>
  );
};

export default ProcessedVideoDisplay;