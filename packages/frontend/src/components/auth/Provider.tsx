// Path: packages/frontend/src/components/auth/Provider.tsx

'use client'

import { SessionProvider } from "next-auth/react"
import { ReactNode } from "react"

export default function AuthProvider({ children }: { children: ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>
}