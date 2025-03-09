// Path: packages/frontend/src/components/LandingPage.tsx

"use client";

import React from "react";
import { BrainCircuit, Film, Wand2, LogIn } from "lucide-react";
import { signIn } from "next-auth/react";
import Footer from "./Footer";

// Effect showcase component
interface EffectShowcaseProps {
  name: string;
  description: string;
  preview: React.ReactNode;
}

const EffectShowcase: React.FC<EffectShowcaseProps> = ({ name, description, preview }) => (
  <div className="bg-white rounded-xl shadow-md overflow-hidden">
    <div className="aspect-video bg-gray-100">{preview}</div>
    <div className="p-4">
      <h3 className="font-semibold text-lg text-orange-900">{name}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  </div>
);

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-amber-50 via-orange-50 to-red-50">
      {/* Hero Section */}
      <section className="py-16 md:py-24">
        <div className="container mx-auto max-w-6xl px-4">
          <div className="flex flex-col items-center text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-orange-900 mb-6">
              Transform Videos with AI-Powered Edge Detection
            </h1>
            <p className="text-xl text-orange-700 max-w-2xl mb-10">
              Turn ordinary videos into artistic masterpieces with our cutting-edge 
              rotoscoping technology. Create stunning visual effects in minutes.
            </p>
            <button
              onClick={() => signIn("google")}
              className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-8 rounded-lg flex items-center gap-2 text-lg shadow-lg transition-colors"
            >
              <LogIn size={20} />
              Get Started
            </button>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-12 bg-orange-50/50">
        <div className="container mx-auto max-w-6xl px-4">
          <h2 className="text-3xl font-bold text-orange-900 text-center mb-12">
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4">
                <LogIn className="w-8 h-8 text-orange-500" />
              </div>
              <h3 className="text-xl font-semibold text-orange-900 mb-2">
                Sign In
              </h3>
              <p className="text-orange-700">
                Create an account or sign in with your Google account to get started.
              </p>
            </div>
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4">
                <Film className="w-8 h-8 text-orange-500" />
              </div>
              <h3 className="text-xl font-semibold text-orange-900 mb-2">
                Upload Video
              </h3>
              <p className="text-orange-700">
                Upload any video file. For best results, use videos under 30 seconds.
              </p>
            </div>
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-orange-100 flex items-center justify-center mb-4">
                <Wand2 className="w-8 h-8 text-orange-500" />
              </div>
              <h3 className="text-xl font-semibold text-orange-900 mb-2">
                Apply Effect
              </h3>
              <p className="text-orange-700">
                Choose from multiple effects and download your transformed video.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Effect Gallery */}
      <section className="py-16">
        <div className="container mx-auto max-w-6xl px-4">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-3xl font-bold text-orange-900">
              Available Effects
            </h2>
            <button
              onClick={() => signIn("google")}
              className="text-orange-500 font-semibold"
            >
              Try Them Now →
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Example effects */}
            <EffectShowcase
              name="Scanner Darkly"
              description="Neural network-based rotoscope effect, similar to the movie"
              preview={
                <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                  <BrainCircuit className="text-orange-300" size={48} />
                </div>
              }
            />
            <EffectShowcase
              name="Silent Movie"
              description="Classic black and white silent film effect with vintage artifacts"
              preview={
                <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                  <Film className="text-orange-300" size={48} />
                </div>
              }
            />
            <EffectShowcase
              name="Technicolor"
              description="Vibrant saturated colors like early color films"
              preview={
                <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                  <Wand2 className="text-orange-300" size={48} />
                </div>
              }
            />
            <EffectShowcase
              name="Grindhouse"
              description="Gritty, vintage exploitation film look with scratches"
              preview={
                <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                  <Film className="text-orange-300" size={48} />
                </div>
              }
            />
          </div>
        </div>
      </section>

      {/* Call To Action */}
      <section className="py-16 bg-orange-100/50">
        <div className="container mx-auto max-w-6xl px-4 text-center">
          <h2 className="text-3xl font-bold text-orange-900 mb-6">
            Ready to Transform Your Videos?
          </h2>
          <p className="text-lg text-orange-700 max-w-2xl mx-auto mb-8">
            Join today and start creating stunning visual effects with our AI-powered tools.
          </p>
          <button
            onClick={() => signIn("google")}
            className="bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-8 rounded-lg flex items-center gap-2 text-lg mx-auto shadow-md transition-colors"
          >
            <LogIn size={20} />
            Sign In with Google
          </button>
        </div>
      </section>

      <Footer />
    </div>
  );
}