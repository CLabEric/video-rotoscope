// src/components/ClientAuthProvider.tsx
"use client"

import { ReactNode } from 'react';
import { AuthProvider } from '@/contexts/AuthContext';

export function ClientAuthProvider({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>;
}