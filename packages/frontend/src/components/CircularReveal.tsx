import React, { useState, useRef, useEffect } from 'react';

interface CircularRevealProps {
  show: boolean;
  x: number;
  y: number;
  children: React.ReactNode;
  className?: string;
}

const CircularReveal: React.FC<CircularRevealProps> = ({
  show,
  x,
  y,
  children,
  className = ''
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [clipPath, setClipPath] = useState('');
  
  useEffect(() => {
    if (!containerRef.current) return;
    
    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    
    // Calculate relative position within container
    const relativeX = x - rect.left;
    const relativeY = y - rect.top;
    
    // Calculate the maximum radius needed
    const maxRadius = Math.sqrt(
      Math.max(
        Math.pow(rect.width, 2) + Math.pow(rect.height, 2)
      )
    );
    
    // Set the clip path based on show state
    setClipPath(`circle(${show ? maxRadius : 0}px at ${relativeX}px ${relativeY}px)`);
  }, [show, x, y]);

  return (
    <div 
      ref={containerRef}
      className={`${className} ${!show ? 'pointer-events-none' : ''}`}
      style={{
        clipPath: clipPath,
        transition: 'clip-path 600ms ease-in-out',
        WebkitClipPath: clipPath,
      }}
    >
      {children}
    </div>
  );
};

export default CircularReveal;