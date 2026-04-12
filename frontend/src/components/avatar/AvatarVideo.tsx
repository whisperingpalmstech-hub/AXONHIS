"use client";
import React, { useRef, useEffect, useState } from "react";

const AVATAR_VIDEO_URL =
  "https://res.cloudinary.com/dnxsyymiq/video/upload/v1775037332/Realistic_Doctor_Avatar_Video_Generation_cwdf7x.mp4";

interface AvatarVideoProps {
  isSpeaking?: boolean;
  className?: string;
}

export function AvatarVideo({ isSpeaking = false, className = "" }: AvatarVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      video.play().catch(() => {});
    }
  }, []);

  return (
    <div className={`avatar-video-container ${className}`}>
      {/* Loading shimmer */}
      {!isLoaded && (
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 animate-pulse flex items-center justify-center z-10">
          <div className="flex flex-col items-center gap-4">
            <div className="w-20 h-20 rounded-full border-4 border-blue-500/30 border-t-blue-500 animate-spin" />
            <p className="text-slate-400 text-sm font-medium">Loading Avatar...</p>
          </div>
        </div>
      )}

      <video
        ref={videoRef}
        src={AVATAR_VIDEO_URL}
        autoPlay
        loop
        muted
        playsInline
        onLoadedData={() => setIsLoaded(true)}
        className="w-full h-full object-cover"
        style={{ filter: isLoaded ? "none" : "blur(20px)" }}
      />

      {/* Speaking glow effect */}
      {isSpeaking && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-blue-500/10 to-transparent animate-pulse" />
          <div className="absolute inset-0 border-2 border-blue-400/20 rounded-none animate-pulse" />
        </div>
      )}
    </div>
  );
}
