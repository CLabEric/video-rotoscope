// Path: packages/frontend/src/components/Header.tsx

'use client'

import { useSession } from "next-auth/react";
import Link from "next/link";
import { BrainCircuit, VideoIcon } from "lucide-react";
import LoginButton from "@/components/auth/LoginButton";

export default function Header() {
  const { data: session } = useSession();
  
  return (
    <header className="w-full bg-gradient-to-br from-amber-50/70 via-orange-50/70 to-red-50/70 backdrop-blur-sm">
      <div className="container mx-auto max-w-6xl px-4 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <Link href="/" className="text-xl sm:text-2xl font-bold text-orange-900">
            Edge Detect Studio
          </Link>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-orange-50 text-orange-800 px-2 py-1 sm:px-3 sm:py-2 rounded-lg">
              <BrainCircuit className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
              <span className="text-xs sm:text-sm">AI-Powered Video Effects</span>
            </div>
            
            {/* Navigation Links for Authenticated Users */}
            {session && (
              <Link 
                href="/dashboard" 
                className="flex items-center gap-2 bg-orange-50 hover:bg-orange-100 text-orange-700 px-3 py-2 rounded-lg transition-colors"
              >
                <VideoIcon size={16} />
                <span>Dashboard</span>
              </Link>
            )}
            
            {/* Login/Logout Button */}
            <LoginButton />
          </div>
        </div>
      </div>
    </header>
  );
}