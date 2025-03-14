"use client"

import React, { createContext, useContext, ReactNode } from 'react';
import { useAuth } from '../hooks/useAuth';

// Define the type for our context using proper TypeScript types
type AuthContextType = {
  user: any; // Use 'any' instead of the FirebaseUser type to avoid import issues
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  userId: string;
}

// Create the context with default values
const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signInWithGoogle: async () => {},
  signOut: async () => {},
  userId: 'anonymous'
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const auth = useAuth();
  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => useContext(AuthContext);