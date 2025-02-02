import React from "react";
import { Github, Twitter, Linkedin, Mail } from "lucide-react";

const Footer: React.FC = () => {
  return (
    <footer className="bg-white/50 backdrop-blur-sm border-t border-orange-100 py-8 mt-8">
      <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          {/* Company/App Info */}
          <div className="text-center md:text-left mb-6 md:mb-0">
            <h3 className="text-2xl font-bold text-orange-900 mb-2">
              Edge Detection Studio
            </h3>
            <p className="text-orange-700 text-sm">
              Transform videos with AI-powered computational vision
            </p>
          </div>

          {/* Social Links */}
          <div className="flex space-x-4">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="
                text-orange-600 hover:text-orange-800 
                bg-orange-100 hover:bg-orange-200 
                p-3 rounded-full 
                transition-all
                flex items-center justify-center
              "
            >
              <Github className="w-5 h-5" />
            </a>
            <a
              href="https://twitter.com"
              target="_blank"
              rel="noopener noreferrer"
              className="
                text-orange-600 hover:text-orange-800 
                bg-orange-100 hover:bg-orange-200 
                p-3 rounded-full 
                transition-all
                flex items-center justify-center
              "
            >
              <Twitter className="w-5 h-5" />
            </a>
            <a
              href="https://linkedin.com"
              target="_blank"
              rel="noopener noreferrer"
              className="
                text-orange-600 hover:text-orange-800 
                bg-orange-100 hover:bg-orange-200 
                p-3 rounded-full 
                transition-all
                flex items-center justify-center
              "
            >
              <Linkedin className="w-5 h-5" />
            </a>
            <a
              href="mailto:contact@edgedetectionstudio.com"
              className="
                text-orange-600 hover:text-orange-800 
                bg-orange-100 hover:bg-orange-200 
                p-3 rounded-full 
                transition-all
                flex items-center justify-center
              "
            >
              <Mail className="w-5 h-5" />
            </a>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-6 border-t border-orange-100 text-center text-sm text-orange-700">
          © {new Date().getFullYear()} Edge Detection Studio. All rights
          reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
