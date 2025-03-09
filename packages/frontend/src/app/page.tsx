// Path: packages/frontend/src/app/page.tsx

import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import LandingPage from "@/components/LandingPage"; 

export default async function Home() {
  // Check if user is logged in
  const session = await getServerSession();
  
  // If logged in, redirect to dashboard
  if (session) {
    redirect("/dashboard");
  }
  
  // If not logged in, show landing page
  return <LandingPage />;
}