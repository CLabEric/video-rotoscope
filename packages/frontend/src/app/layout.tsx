// Path: packages/frontend/src/app/layout.tsx

import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import AuthProvider from "@/components/auth/Provider";
import Header from "@/components/Header"; // Add this import

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Video Edge Detection",
  description: "Transform your videos with real-time edge detection",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <Header /> {/* Add the Header component here */}
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}