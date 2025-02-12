import { AlertCircle } from 'lucide-react';

const StorageNotice = () => {
  return (
    <div className="mt-4 bg-orange-50 border border-orange-200 rounded-lg p-4 flex items-start gap-3">
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
};

export default StorageNotice;