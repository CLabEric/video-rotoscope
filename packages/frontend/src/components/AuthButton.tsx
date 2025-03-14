// src/components/AuthButton.tsx
"use client";

import React from 'react';
import { useAuthContext } from '../contexts/AuthContext';

const AuthButton = () => {
  const { user, loading, signInWithGoogle, signOut } = useAuthContext();

  if (loading) {
    return <div className="animate-pulse bg-orange-100 p-2 rounded-md w-24 h-8"></div>;
  }

  if (user) {
    return (
      <div className="flex items-center gap-3">
        {user.photoURL && (
          <img 
            src={user.photoURL} 
            alt={user.displayName || 'User'} 
            className="w-8 h-8 rounded-full"
          />
        )}
        <div className="text-sm text-gray-600">{user.displayName || user.email}</div>
        <button
          onClick={() => signOut()}
          className="bg-orange-100 hover:bg-orange-200 text-orange-600 px-3 py-1 rounded-md text-sm transition-colors"
        >
          Sign Out
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => signInWithGoogle()}
      className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded-md text-sm transition-colors"
    >
      Sign In
    </button>
  );
};

export default AuthButton;