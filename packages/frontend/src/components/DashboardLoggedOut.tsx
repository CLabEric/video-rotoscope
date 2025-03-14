// src/components/DashboardLoggedOut.tsx
"use client";

import React from 'react';
import { useAuthContext } from "@/contexts/AuthContext";
import { Film, Lock, Video, Play, ArrowRight } from "lucide-react";

const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <div className="bg-white p-6 rounded-xl shadow-md border border-orange-100">
    <div className="bg-orange-100 w-12 h-12 rounded-full flex items-center justify-center mb-4">
      {icon}
    </div>
    <h3 className="text-lg font-semibold text-orange-900 mb-2">{title}</h3>
    <p className="text-orange-700 text-sm">{description}</p>
  </div>
);

const DashboardLoggedOut: React.FC = () => {
  const { signInWithGoogle } = useAuthContext();

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl overflow-hidden shadow-lg mb-12">
        <div className="p-8 md:p-12">
          <div className="max-w-xl">
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Transform Your Videos with AI
            </h1>
            <p className="text-orange-100 mb-8">
              Sign in to access your personal dashboard and start creating stunning visual effects with our AI-powered video processing.
            </p>
            <div className="bg-white/10 p-4 rounded-lg backdrop-blur-sm border border-white/20 mb-6">
              <div className="flex items-center gap-3">
                <Lock className="w-5 h-5 text-white flex-shrink-0" />
                <p className="text-white text-sm">
                  Your videos are private and automatically deleted after 24 hours.
                </p>
              </div>
            </div>
            <button
              onClick={signInWithGoogle}
              className="flex items-center gap-2 bg-white text-orange-600 hover:bg-orange-50 px-6 py-3 rounded-lg font-medium transition-colors"
            >
              Sign in to Continue
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
        <div className="flex overflow-hidden h-20 bg-orange-600 relative">
          {Array.from({ length: 20 }).map((_, i) => (
            <div key={i} 
              className="flex-shrink-0 h-full w-16 md:w-24 border-r border-orange-500/50 flex items-center justify-center"
              style={{ opacity: 0.1 + (i % 5) * 0.2 }}
            >
              <Film className="w-8 h-8 text-white" />
            </div>
          ))}
          <div className="absolute inset-0 bg-gradient-to-r from-orange-600 via-transparent to-orange-600" />
        </div>
      </div>

      <h2 className="text-2xl font-bold text-orange-900 mb-6 text-center">
        What You Can Do
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <FeatureCard
          icon={<Video className="w-6 h-6 text-orange-600" />}
          title="Process Any Video"
          description="Upload videos from your device and transform them with powerful visual effects."
        />
        <FeatureCard
          icon={<Play className="w-6 h-6 text-orange-600" />}
          title="AI-Powered Effects"
          description="Apply neural network-based rotoscoping and other advanced effects with a single click."
        />
        <FeatureCard
          icon={<Film className="w-6 h-6 text-orange-600" />}
          title="Manage Your Collection"
          description="Access all your processed videos in one place and download them to keep forever."
        />
      </div>

      <div className="text-center">
        <button
          onClick={signInWithGoogle}
          className="inline-flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-medium transition-colors"
        >
          Sign in with Google
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default DashboardLoggedOut;