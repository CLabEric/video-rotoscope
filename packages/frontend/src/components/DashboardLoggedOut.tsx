// packages/frontend/src/components/DashboardLoggedOut.tsx
"use client";

import React, { useState } from 'react';
import { useAuthContext } from "@/contexts/AuthContext";
import { ArrowRight, Play, Check } from "lucide-react";

interface EffectButtonProps {
  name: string;
  description: string;
  isActive: boolean;
  onClick: () => void;
}

type EffectType = "scanner-darkly" | "silent-movie" | "technicolor";

interface EffectInfo {
  name: string;
  description: string;
}

const EffectButton: React.FC<EffectButtonProps> = ({ name, description, isActive, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-start text-left p-4 rounded-lg transition-all w-full ${
      isActive 
        ? "bg-orange-100 border-2 border-orange-300 shadow-md" 
        : "bg-white border border-gray-200 hover:border-orange-200 hover:bg-orange-50"
    }`}
  >
    <div className="flex-grow">
      <div className="flex items-center gap-2">
        {isActive && <Check className="w-4 h-4 text-orange-500" />}
        <h3 className="font-medium text-gray-900">{name}</h3>
      </div>
      <p className="text-xs text-gray-600 mt-1">{description}</p>
    </div>
  </button>
);

const DashboardLoggedOut: React.FC = () => {
  const { signInWithGoogle } = useAuthContext();
  const [activeEffect, setActiveEffect] = useState<EffectType>("silent-movie");
  
  const effectDetails: Record<EffectType, EffectInfo> = {
    "scanner-darkly": {
      name: "Scanner Darkly",
      description: "Neural network-based rotoscoping effect with edge detection and color quantization."
    },
    "silent-movie": {
      name: "Silent Movie",
      description: "Classic black and white silent film effect with vintage artifacts and film grain."
    },
    "technicolor": {
      name: "Technicolor",
      description: "Vibrant saturated colors like early color films from the golden age of cinema."
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Left Column - Technical Drawing and Text */}
        <div className="md:col-span-1">
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200 mb-6">
            <img 
              src="/technical-illustration.png" 
              alt="Technical Drawing of Animation Device" 
              className="w-full h-auto object-contain mb-4"
            />
            <h3 className="text-sm font-semibold text-gray-900">Traditional Animation Technique</h3>
            <p className="text-xs text-gray-600">
              Based on rotoscoping technology first patented in 1917, now powered by neural networks
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
            <h2 className="font-bold text-gray-900 mb-4">Choose an Effect:</h2>
            <div className="space-y-3">
              <EffectButton 
                name="Scanner Darkly" 
                description="Neural network rotoscoping"
                isActive={activeEffect === "scanner-darkly"}
                onClick={() => setActiveEffect("scanner-darkly")}
              />
              <EffectButton 
                name="Silent Movie" 
                description="Classic black & white"
                isActive={activeEffect === "silent-movie"}
                onClick={() => setActiveEffect("silent-movie")}
              />
              <EffectButton 
                name="Technicolor" 
                description="Vibrant color processing"
                isActive={activeEffect === "technicolor"}
                onClick={() => setActiveEffect("technicolor")}
              />
            </div>
            
            <button
              onClick={signInWithGoogle}
              className="mt-6 bg-orange-500 hover:bg-orange-600 text-white px-5 py-3 rounded-lg font-medium transition-all w-full flex items-center justify-center gap-2"
            >
              Sign in to Start
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Right Column - Video Comparison */}
        <div className="md:col-span-2">
          <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200 h-full">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Transform Your Videos with AI
            </h1>
            <p className="text-gray-600 mb-6">
              Apply professional-grade effects including rotoscoping, film emulation, and more. See the comparison below.
            </p>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-900 rounded-lg overflow-hidden">
                <div className="bg-gray-800 text-gray-200 text-sm font-medium p-2">
                  Original Video
                </div>
                <div className="aspect-video">
                  <img 
                    src="/example-effects/original.png" 
                    alt="Original video" 
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
              
              <div className="bg-gray-900 rounded-lg overflow-hidden">
                <div className="bg-gray-800 text-gray-200 text-sm font-medium p-2 flex items-center justify-between">
                  <span>{effectDetails[activeEffect].name}</span>
                  <div className="bg-orange-500 text-white text-xs px-2 py-0.5 rounded">
                    AI-Powered
                  </div>
                </div>
                <div className="aspect-video">
                  <img 
                    src={`/example-effects/${activeEffect}.png`} 
                    alt="Processed video" 
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            </div>
            
            <div className="bg-orange-50 border border-orange-100 rounded-lg p-4">
              <h3 className="font-semibold text-orange-800 mb-1">About {effectDetails[activeEffect].name}</h3>
              <p className="text-orange-700 text-sm">
                {effectDetails[activeEffect].description} This effect transforms your videos into stunning artistic creations with just a few clicks.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardLoggedOut;