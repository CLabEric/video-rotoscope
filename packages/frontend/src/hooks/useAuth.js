// src/hooks/useAuth.js
"use client"

import { useState, useEffect } from 'react';
import { 
  onAuthStateChanged, 
  signInWithPopup, 
  GoogleAuthProvider,
  signOut as firebaseSignOut
} from 'firebase/auth';
import { auth } from '../lib/firebase/config';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // This sets up the auth state listener
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });
    
    // Clean up subscription on unmount
    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (error) {
      console.error('Error signing in with Google', error);
    }
  };

  const signOut = async () => {
    try {
      await firebaseSignOut(auth);
    } catch (error) {
      console.error('Error signing out', error);
    }
  };

  return {
    user,
    loading,
    signInWithGoogle,
    signOut,
    userId: user?.uid || 'anonymous'
  };
}