// src/app/page.tsx
"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // Check for auth on client side
    const hasFirebaseToken = document.cookie.includes('firebase-auth-token');
    if (hasFirebaseToken) {
      router.push("/dashboard");
    }
  }, [router]);
  
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-grow container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-orange-900 mb-6">
            Transform Your Videos with AI Edge Detection
          </h1>
          <p className="text-lg text-orange-700 mb-8">
            Apply professional-grade effects including Scanner Darkly rotoscoping, film emulation, and more.
          </p>
          <Link
            href="/dashboard"
            className="inline-block bg-orange-500 hover:bg-orange-600 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            Get Started
          </Link>
        </div>
      </main>
    </div>
  );
}