// Path: packages/frontend/src/components/auth/LoginButton.tsx

'use client'

import { signIn, signOut, useSession } from "next-auth/react";
import { LogIn, LogOut, User } from "lucide-react";

export default function LoginButton() {
  const { data: session, status } = useSession();
  const loading = status === "loading";

  // Handle login
  const handleLogin = () => {
    signIn("google");
  };

  // Handle logout
  const handleLogout = () => {
    signOut();
  };

  if (loading) {
    return (
      <button className="flex items-center gap-2 bg-gray-100 text-gray-700 px-3 py-2 rounded-lg opacity-70">
        <div className="w-4 h-4 border-2 border-t-transparent border-gray-700 rounded-full animate-spin"></div>
        <span>Loading...</span>
      </button>
    );
  }

  if (session) {
    return (
      <div className="flex items-center gap-3">
        {session.user?.image ? (
          <img 
            src={session.user.image} 
            alt={session.user.name || "User"} 
            className="w-8 h-8 rounded-full" 
          />
        ) : (
          <div className="w-8 h-8 bg-orange-100 text-orange-800 rounded-full flex items-center justify-center">
            <User size={16} />
          </div>
        )}
        <button 
          onClick={handleLogout}
          className="flex items-center gap-2 bg-orange-50 hover:bg-orange-100 text-orange-700 px-3 py-2 rounded-lg transition-colors"
        >
          <LogOut size={16} />
          <span>Sign out</span>
        </button>
      </div>
    );
  }

  return (
    <button 
      onClick={handleLogin}
      className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white px-3 py-2 rounded-lg transition-colors"
    >
      <LogIn size={16} />
      <span>Sign in</span>
    </button>
  );
}