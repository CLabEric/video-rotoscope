import React from "react";
import { Wand2 } from "lucide-react";

interface Effect {
  id: string;
  name: string;
  description: string;
  preview: () => React.ReactNode;
  processingTime?: string;
  type: "ffmpeg" | "neural";
}

interface EffectSelectorProps {
  selectedEffect: string;
  onEffectChange: (effectId: string) => void;
}

const effects: Effect[] = [
  {
    id: "silent-movie",
    name: "Silent Movie",
    description: "Classic black and white silent film effect with vintage artifacts",
    type: "ffmpeg",
    processingTime: "~1 min",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="vintage">
            <feColorMatrix type="matrix" values="0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0.33 0.33 0.33 0 0 0 0 0 1 0"/>
            <feComponentTransfer>
              <feFuncR type="linear" slope="1.2" intercept="-0.1"/>
              <feFuncG type="linear" slope="1.2" intercept="-0.1"/>
              <feFuncB type="linear" slope="1.2" intercept="-0.1"/>
            </feComponentTransfer>
            <feGaussianBlur stdDeviation="0.5"/>
          </filter>
          <pattern id="noise" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
            <image href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAALElEQVQIW2NkQAP/////z4gsBhYAAZggTADGBgGYIEwAxgYBmCBMAMYGAQB9fxQC7vz4EwAAAABJRU5ErkJggg==" x="0" y="0" width="100" height="100"/>
          </pattern>
        </defs>
        
        {/* Background */}
        <rect width="160" height="90" fill="#1a1a1a"/>
        
        {/* Sample scene with vintage effect */}
        <g filter="url(#vintage)">
          <circle cx="80" cy="45" r="25" fill="#e0e0e0"/>
          <rect x="30" y="35" width="100" height="40" rx="5" fill="#c0c0c0"/>
        </g>
        
        {/* Film grain overlay */}
        <rect width="160" height="90" fill="url(#noise)" opacity="0.1"/>
        
        {/* Vignette effect */}
        <radialGradient id="vignette" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="transparent"/>
          <stop offset="100%" stopColor="rgba(0,0,0,0.5)"/>
        </radialGradient>
        <rect width="160" height="90" fill="url(#vignette)"/>
        
        {/* Vertical scratches */}
        <line x1="35" y1="0" x2="35" y2="90" stroke="white" strokeWidth="1" opacity="0.3" />
        <line x1="120" y1="0" x2="120" y2="90" stroke="white" strokeWidth="2" opacity="0.2" />
      </svg>
    ),
  },
  {
    id: "grindhouse",
    name: "Grindhouse",
    description: "Gritty, vintage exploitation film look with scratches",
    type: "ffmpeg",
    processingTime: "~1 min",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="high-contrast">
            <feComponentTransfer>
              <feFuncR type="linear" slope="2" intercept="-0.5"/>
              <feFuncG type="linear" slope="2" intercept="-0.5"/>
              <feFuncB type="linear" slope="2" intercept="-0.5"/>
            </feComponentTransfer>
            <feConvolveMatrix order="3" kernelMatrix="1 -1 1 -1 1 -1 1 -1 1" />
          </filter>
        </defs>
        
        {/* Background */}
        <rect width="160" height="90" fill="#2a2a2a"/>
        
        {/* Sample scene with high contrast effect */}
        <g filter="url(#high-contrast)">
          <circle cx="80" cy="45" r="25" fill="#808080"/>
          <rect x="30" y="35" width="100" height="40" rx="5" fill="#a0a0a0"/>
        </g>
        
        {/* Vertical scratches */}
        <line x1="55" y1="0" x2="55" y2="90" stroke="white" strokeWidth="1" opacity="0.4" />
        <line x1="140" y1="0" x2="140" y2="90" stroke="white" strokeWidth="2" opacity="0.3" />
      </svg>
    ),
  },
  {
    id: "technicolor",
    name: "Technicolor",
    description: "Vibrant saturated colors like early color films",
    type: "ffmpeg",
    processingTime: "~1 min",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="technicolor">
            <feColorMatrix type="matrix" 
              values="1.3 0.1 0.1 0 0
                      0.1 1.1 0.1 0 0
                      0.1 0.1 1.4 0 0
                      0   0   0   1 0"/>
            <feComponentTransfer>
              <feFuncR type="linear" slope="1.2" intercept="0"/>
              <feFuncG type="linear" slope="1.1" intercept="0"/>
              <feFuncB type="linear" slope="1.3" intercept="0"/>
            </feComponentTransfer>
            <feGaussianBlur stdDeviation="0.3"/>
          </filter>
          <pattern id="grain" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
            <image href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAALElEQVQIW2NkQAP/////z4gsBhYAAZggTADGBgGYIEwAxgYBmCBMAMYGAQB9fxQC7vz4EwAAAABJRU5ErkJggg==" x="0" y="0" width="100" height="100"/>
          </pattern>
        </defs>
        
        {/* Background */}
        <rect width="160" height="90" fill="#1a1a1a"/>
        
        {/* Sample scene with technicolor effect */}
        <g filter="url(#technicolor)">
          <circle cx="80" cy="45" r="25" fill="#e05050"/>
          <rect x="30" y="35" width="100" height="40" rx="5" fill="#50a0e0"/>
        </g>
        
        {/* Film grain overlay */}
        <rect width="160" height="90" fill="url(#grain)" opacity="0.07"/>
        
        {/* Vignette effect */}
        <radialGradient id="tech-vignette" cx="50%" cy="50%" r="65%">
          <stop offset="0%" stopColor="transparent"/>
          <stop offset="100%" stopColor="rgba(0,0,0,0.3)"/>
        </radialGradient>
        <rect width="160" height="90" fill="url(#tech-vignette)"/>
        
        {/* Vertical scratch */}
        <line x1="95" y1="0" x2="95" y2="90" stroke="white" strokeWidth="1" opacity="0.3" />
      </svg>
    ),
  },
  {
    id: "scanner-darkly",
    name: "Scanner Darkly",
    description: "Neural network-based rotoscope effect, similar to the movie",
    type: "neural",
    processingTime: "~3-5 min",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="scanner-darkly-filter">
            <feGaussianBlur stdDeviation="0.5" />
            <feColorMatrix type="matrix" 
              values="1.5 0   0   0 0
                      0   1.5 0   0 0
                      0   0   1.5 0 0
                      0   0   0   1 0"/>
            <feComponentTransfer>
              <feFuncR type="discrete" tableValues="0 0.2 0.4 0.6 0.8 1" />
              <feFuncG type="discrete" tableValues="0 0.25 0.5 0.75 1" />
              <feFuncB type="discrete" tableValues="0 0.3 0.6 0.9 1" />
            </feComponentTransfer>
          </filter>
          <pattern id="scanner-grain" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
            <image href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAALElEQVQIW2NkQAP/////z4gsBhYAAZggTADGBgGYIEwAxgYBmCBMAMYGAQB9fxQC7vz4EwAAAABJRU5ErkJggg==" x="0" y="0" width="100" height="100"/>
          </pattern>
        </defs>
        
        {/* Background */}
        <rect width="160" height="90" fill="#f5f5f5"/>
        
        {/* Main elements */}
        <g filter="url(#scanner-darkly-filter)">
          <circle cx="80" cy="45" r="25" fill="#5d8aa8"/>
          <rect x="30" y="35" width="100" height="40" rx="5" fill="#e9967a"/>
        </g>

        {/* Edge outlines - black lines around edges */}
        <circle cx="80" cy="45" r="25" fill="none" stroke="black" strokeWidth="2" />
        <rect x="30" y="35" width="100" height="40" rx="5" fill="none" stroke="black" strokeWidth="2" />
        
        {/* Subtle grain for hand-drawn effect */}
        <rect width="160" height="90" fill="url(#scanner-grain)" opacity="0.05"/>
      </svg>
    ),
  }
];

const EffectSelector: React.FC<EffectSelectorProps> = ({
  selectedEffect,
  onEffectChange,
}) => {
  return (
    <div className="w-full space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Wand2 className="w-5 h-5 text-orange-500" />
        <h3 className="text-lg font-semibold text-gray-900">Choose Effect</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {effects.map((effect) => (
          <div key={effect.id} className="flex flex-col">
            <button
              onClick={() => onEffectChange(effect.id)}
              className={`
                group relative rounded-xl transition-all 
                flex flex-col h-full
                ${
                  selectedEffect === effect.id
                    ? "ring-2 ring-orange-500 ring-offset-2"
                    : "hover:bg-orange-50"
                }
              `}
            >
              {/* Preview Container */}
              <div className="aspect-video w-full overflow-hidden rounded-t-xl bg-gray-900">
                {effect.preview()}
              </div>

              {/* Effect Info */}
              <div className="p-4 text-left">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-medium text-gray-900 text-base">
                    {effect.name}
                  </h4>
                  
                  {/* Tag for effect type */}
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    effect.type === "neural" 
                      ? "bg-purple-100 text-purple-800"
                      : "bg-blue-100 text-blue-800"
                  }`}>
                    {effect.type === "neural" ? "AI" : "FFmpeg"}
                  </span>
                </div>
                
                <p className="text-sm text-gray-500 mb-1">
                  {effect.description}
                </p>
                
                {effect.processingTime && (
                  <p className="text-xs text-gray-400">
                    Processing: {effect.processingTime}
                  </p>
                )}
              </div>

              {/* Selected Indicator */}
              {selectedEffect === effect.id && (
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-white shadow-lg">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M13.3332 4L5.99984 11.3333L2.6665 8"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              )}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EffectSelector;