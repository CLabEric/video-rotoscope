"use client"

import React from 'react';
import Link from 'next/link';
import AuthButton from './AuthButton';

const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full bg-white/95 backdrop-blur-sm border-b border-orange-100">
      <div className="container mx-auto max-w-6xl px-4 py-3 flex justify-between items-center">
        <Link href="/" className="font-semibold text-lg text-orange-900">
          Video Rotoscope
        </Link>
        
        <AuthButton />
      </div>
    </header>
  );
};

export default Header;