// src/components/PaymentModal.tsx
import React from 'react';
import { X } from 'lucide-react';
import stripePromise from '@/lib/stripe';

interface PaymentModalProps {
  amount: number;
  effectType: string;
  videoKey: string;
  onClose: () => void;
  onSuccess: (videoKey: string, effectType: string) => void;
}

const PaymentModal: React.FC<PaymentModalProps> = ({ 
  amount, 
  effectType, 
  videoKey, 
  onClose, 
  onSuccess 
}) => {
  const [isProcessing, setIsProcessing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // For demo purposes - simulate a payment
  const handlePaymentClick = async () => {
    try {
      setIsProcessing(true);
      setError(null);
      
      // In a real implementation, you would use Stripe Elements here
      // This is just a simulation for demo purposes
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Payment successful
      onSuccess(videoKey, effectType);
    } catch (err) {
      setError('Payment processing failed. Please try again.');
      console.error('Payment error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl max-w-md w-full p-6 relative">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
        >
          <X className="w-5 h-5" />
        </button>
        
        <h2 className="text-xl font-bold text-orange-900 mb-6">Complete Your Purchase</h2>
        
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-700">Effect Type</span>
            <span className="font-medium">{effectType}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Price</span>
            <span className="font-bold text-lg">${amount.toFixed(2)}</span>
          </div>
        </div>
        
        {error && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}
        
        <button
          onClick={handlePaymentClick}
          disabled={isProcessing}
          className="w-full bg-orange-500 hover:bg-orange-600 text-white py-3 px-4 rounded-lg transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {isProcessing ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
              Processing...
            </div>
          ) : (
            `Pay $${amount.toFixed(2)}`
          )}
        </button>
        
        <p className="text-xs text-gray-500 mt-4 text-center">
          This is a simulation. In production, this would use Stripe Elements for secure payment processing.
        </p>
      </div>
    </div>
  );
};

export default PaymentModal;