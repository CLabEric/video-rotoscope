// src/app/layout.tsx
import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClientAuthProvider } from "@/components/ClientAuthProvider";
import Header from "@/components/Header";

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
        <ClientAuthProvider>
          <Header />
          {children}
        </ClientAuthProvider>
      </body>
    </html>
  );
}