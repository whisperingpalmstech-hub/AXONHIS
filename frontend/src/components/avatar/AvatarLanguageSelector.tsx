"use client";
import React, { useState, useRef, useEffect } from "react";
import { SUPPORTED_LANGUAGES } from "@/i18n";

interface AvatarLanguageSelectorProps {
  currentLanguage: string;
  onLanguageChange: (code: string) => void;
}

export function AvatarLanguageSelector({ currentLanguage, onLanguageChange }: AvatarLanguageSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = SUPPORTED_LANGUAGES.find(l => l.code === currentLanguage) || SUPPORTED_LANGUAGES[0];

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="
          flex items-center gap-2 px-3 py-2 rounded-xl
          bg-white/10 hover:bg-white/20 backdrop-blur-md
          border border-white/15 hover:border-white/30
          transition-all duration-200
        "
      >
        <span className="text-base">{current.flag}</span>
        <span className="text-xs font-medium text-white/80">{current.name}</span>
        <svg className={`w-3 h-3 text-white/50 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {open && (
        <div className="
          absolute right-0 top-full mt-2 w-52
          bg-slate-900/95 backdrop-blur-xl
          border border-white/10 rounded-xl
          shadow-2xl shadow-black/50
          overflow-hidden z-50
          animate-in
        ">
          <div className="py-1 max-h-80 overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/20">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => { onLanguageChange(lang.code); setOpen(false); }}
                className={`
                  w-full flex items-center gap-3 px-4 py-2.5
                  hover:bg-white/10 transition-colors text-left
                  ${lang.code === currentLanguage ? "bg-blue-500/20 text-blue-300" : "text-white/70"}
                `}
              >
                <span className="text-lg">{lang.flag}</span>
                <div className="flex-1">
                  <p className="text-xs font-medium">{lang.name}</p>
                  <p className="text-[10px] text-white/40">{lang.nativeName}</p>
                </div>
                {lang.code === currentLanguage && (
                  <svg className="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
