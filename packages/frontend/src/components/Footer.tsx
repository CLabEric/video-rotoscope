import React from "react";
import { Github, Twitter, Linkedin, Mail } from "lucide-react";

const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-white/50 backdrop-blur-sm border-t border-orange-100">
      <div className="container mx-auto max-w-6xl px-4 py-4">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-center md:text-left">
            <h3 className="text-lg font-bold text-orange-900">
              Edge Detection Studio
            </h3>
            <p className="text-orange-700 text-sm">
              Transform videos with AI-powered computational vision
            </p>
          </div>

          <div className="flex gap-3">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-orange-600 hover:text-orange-800 bg-orange-100 hover:bg-orange-200 p-2 rounded-full transition-all"
            >
              <Github className="w-5 h-5" />
            </a>
            <a
              href="https://twitter.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-orange-600 hover:text-orange-800 bg-orange-100 hover:bg-orange-200 p-2 rounded-full transition-all"
            >
              <Twitter className="w-5 h-5" />
            </a>
            <a
              href="https://linkedin.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-orange-600 hover:text-orange-800 bg-orange-100 hover:bg-orange-200 p-2 rounded-full transition-all"
            >
              <Linkedin className="w-5 h-5" />
            </a>
            <a
              href="mailto:contact@edgedetectionstudio.com"
              className="text-orange-600 hover:text-orange-800 bg-orange-100 hover:bg-orange-200 p-2 rounded-full transition-all"
            >
              <Mail className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;