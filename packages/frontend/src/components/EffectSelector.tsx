import React from "react";
import { Wand2 } from "lucide-react";

// Define types for the effect
interface Effect {
  id: string;
  name: string;
  description: string;
  color: string;
  preview: () => React.ReactNode;
}

// Define prop types
interface EffectSelectorProps {
  selectedEffect: string;
  onEffectChange: (effectId: string) => void;
}

const effects: Effect[] = [
  {
    id: "edge",
    name: "Edge Detection",
    description: "FFmpeg edge detection filter with color mix mode",
    color: "blue",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="ffmpeg-edge">
            <feColorMatrix
              type="matrix"
              values="0 0 0 0 0   0 0 0 0 0   0 0 0 0 0  -1 -1 -1 1 0"
              result="dark"
            />
            <feGaussianBlur stdDeviation="0.5" result="blur" />
            <feColorMatrix
              type="matrix"
              values="1 0 0 0 0   0 1 0 0 0   0 0 1 0 0  0 0 0 15 -3"
              result="edges"
            />
            <feBlend mode="screen" in="edges" in2="blur" />
          </filter>
        </defs>
        <rect width="160" height="90" fill="#1f2937" />

        <g filter="url(#ffmpeg-edge)">
          <path
            d="M80,20 C100,20 115,35 115,55 C115,75 100,90 80,90 C60,90 45,75 45,55 C45,35 60,20 80,20"
            fill="#6b7280"
          />
          <circle cx="65" cy="45" r="5" fill="#6b7280" />
          <circle cx="95" cy="45" r="5" fill="#6b7280" />
          <path
            d="M75,55 Q80,60 85,55"
            strokeWidth="3"
            stroke="#6b7280"
            fill="none"
          />
          <path
            d="M70,65 Q80,72 90,65"
            strokeWidth="3"
            stroke="#6b7280"
            fill="none"
          />
        </g>
      </svg>
    ),
  },
  {
    id: "cartoon",
    name: "Cartoon",
    description: "Posterization with edge enhancement",
    color: "purple",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="ffmpeg-cartoon">
            <feGaussianBlur stdDeviation="0.5" result="blur" />
            <feColorMatrix
              type="matrix"
              values="0.3333 0.3333 0.3333 0 0
                      0.3333 0.3333 0.3333 0 0
                      0.3333 0.3333 0.3333 0 0
                      0      0      0      1 0"
              result="grayscale"
            />
            <feComponentTransfer result="posterize">
              <feFuncR type="discrete" tableValues="0 0.25 0.5 0.75 1" />
              <feFuncG type="discrete" tableValues="0 0.25 0.5 0.75 1" />
              <feFuncB type="discrete" tableValues="0 0.25 0.5 0.75 1" />
            </feComponentTransfer>
          </filter>
          <filter id="cartoon-edges">
            <feMorphology operator="dilate" radius="0.5" />
            <feColorMatrix
              type="matrix"
              values="1 0 0 0 0   0 1 0 0 0   0 0 1 0 0  0 0 0 30 -15"
            />
          </filter>
        </defs>
        <rect width="160" height="90" fill="#1f2937" />

        <g filter="url(#ffmpeg-cartoon)">
          <path
            d="M80,20 C100,20 115,35 115,55 C115,75 100,90 80,90 C60,90 45,75 45,55 C45,35 60,20 80,20"
            fill="#c4b5fd"
          />
        </g>

        <g filter="url(#cartoon-edges)">
          <path
            d="M80,20 C100,20 115,35 115,55 C115,75 100,90 80,90 C60,90 45,75 45,55 C45,35 60,20 80,20"
            stroke="#4c1d95"
            strokeWidth="1"
            fill="none"
          />
          <circle
            cx="65"
            cy="45"
            r="5"
            stroke="#4c1d95"
            strokeWidth="1"
            fill="none"
          />
          <circle
            cx="95"
            cy="45"
            r="5"
            stroke="#4c1d95"
            strokeWidth="1"
            fill="none"
          />
          <path
            d="M70,65 Q80,72 90,65"
            stroke="#4c1d95"
            strokeWidth="1"
            fill="none"
          />
        </g>
      </svg>
    ),
  },
  {
    id: "canny",
    name: "Canny Edge",
    description: "Precise edge detection using Canny algorithm",
    color: "yellow",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="canny-edge">
            <feGaussianBlur stdDeviation="0.5" result="blur" />
            <feColorMatrix
              type="matrix"
              values="2 -1 -1 0 0
                     -1  2 -1 0 0
                     -1 -1  2 0 0
                      0  0  0 1 0"
              result="sharpen"
            />
            <feComponentTransfer result="threshold">
              <feFuncR type="linear" slope="5" intercept="-1" />
              <feFuncG type="linear" slope="5" intercept="-1" />
              <feFuncB type="linear" slope="5" intercept="-1" />
            </feComponentTransfer>
          </filter>
        </defs>
        <rect width="160" height="90" fill="#000000" />

        <g filter="url(#canny-edge)">
          <path
            d="M80,20 C100,20 115,35 115,55 C115,75 100,90 80,90 C60,90 45,75 45,55 C45,35 60,20 80,20"
            stroke="#ffffff"
            strokeWidth="1"
            fill="none"
          />
          <circle
            cx="65"
            cy="45"
            r="5"
            stroke="#ffffff"
            strokeWidth="1"
            fill="none"
          />
          <circle
            cx="95"
            cy="45"
            r="5"
            stroke="#ffffff"
            strokeWidth="1"
            fill="none"
          />
          <path
            d="M70,65 Q80,72 90,65"
            stroke="#ffffff"
            strokeWidth="1"
            fill="none"
          />
        </g>
      </svg>
    ),
  },
  {
    id: "sobel",
    name: "Sobel Filter",
    description: "Directional edge detection",
    color: "green",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="sobel-edge">
            <feConvolveMatrix
              order="3"
              kernelMatrix="1 2 1
                           0 0 0
                          -1 -2 -1"
              preserveAlpha="true"
              result="vertical"
            />
            <feConvolveMatrix
              order="3"
              kernelMatrix="1 0 -1
                           2 0 -2
                           1 0 -1"
              preserveAlpha="true"
              result="horizontal"
            />
            <feBlend mode="screen" in="vertical" in2="horizontal" />
          </filter>
        </defs>
        <rect width="160" height="90" fill="#1f2937" />

        <g filter="url(#sobel-edge)">
          <path
            d="M80,20 C100,20 115,35 115,55 C115,75 100,90 80,90 C60,90 45,75 45,55 C45,35 60,20 80,20"
            fill="#6b7280"
          />
          <circle cx="65" cy="45" r="5" fill="#6b7280" />
          <circle cx="95" cy="45" r="5" fill="#6b7280" />
          <path
            d="M70,65 Q80,72 90,65"
            strokeWidth="3"
            stroke="#6b7280"
            fill="none"
          />
        </g>
      </svg>
    ),
  },
  {
    id: "highpass",
    name: "High Pass",
    description: "Enhanced edge and detail detection",
    color: "sky",
    preview: () => (
      <svg viewBox="0 0 160 90" className="w-full h-full">
        <defs>
          <filter id="high-pass">
            <feGaussianBlur stdDeviation="1" result="blur" />
            <feColorMatrix
              type="matrix"
              values="1 0 0 0 0
                     0 1 0 0 0
                     0 0 1 0 0
                     0 0 0 1 0"
              in="SourceGraphic"
              result="original"
            />
            <feColorMatrix
              type="matrix"
              values="1 0 0 0 0
                     0 1 0 0 0
                     0 0 1 0 0
                     0 0 0 1 0"
              in="blur"
              result="blurred"
            />
            <feComposite
              operator="arithmetic"
              k1="1"
              k2="-1"
              in="original"
              in2="blurred"
            />
          </filter>
        </defs>
        <rect width="160" height="90" fill="#1f2937" />

        <g filter="url(#high-pass)">
          <path
            d="M80,20 C100,20 115,35 115,55 C115,75 100,90 80,90 C60,90 45,75 45,55 C45,35 60,20 80,20"
            fill="#93c5fd"
          />
          <circle cx="65" cy="45" r="5" fill="#93c5fd" />
          <circle cx="95" cy="45" r="5" fill="#93c5fd" />
          <path
            d="M70,65 Q80,72 90,65"
            strokeWidth="3"
            stroke="#93c5fd"
            fill="none"
          />
        </g>
      </svg>
    ),
  },
];

const EffectSelector: React.FC<EffectSelectorProps> = ({
  selectedEffect,
  onEffectChange,
}) => {
  return (
    <div className="w-full space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <Wand2 className="w-5 h-5 text-blue-500" />
        <h3 className="text-lg font-semibold text-gray-900">Choose Effect</h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {effects.map((effect) => (
          <div key={effect.id} className="flex flex-col">
            <button
              onClick={() => onEffectChange(effect.id)}
              className={`
                group relative rounded-xl transition-all 
                flex flex-col h-full
                ${
                  selectedEffect === effect.id
                    ? "ring-2 ring-blue-500 ring-offset-2"
                    : "hover:bg-gray-50"
                }
              `}
            >
              {/* Preview Container */}
              <div className="aspect-video w-full overflow-hidden rounded-t-xl bg-gray-900">
                {effect.preview()}
              </div>

              {/* Effect Info */}
              <div className="p-3 text-left flex-grow flex flex-col">
                <h4 className="font-medium text-gray-900 mb-1 text-sm sm:text-base">
                  {effect.name}
                </h4>
                <p className="text-xs sm:text-sm text-gray-500 flex-grow hidden sm:block">
                  {effect.description}
                </p>
              </div>

              {/* Selected Indicator */}
              {selectedEffect === effect.id && (
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white shadow-lg">
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
