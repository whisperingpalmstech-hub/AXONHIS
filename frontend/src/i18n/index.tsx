"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

// ─── Language Configuration ───────────────────────────────────────
export interface LanguageConfig {
  code: string;
  name: string;
  nativeName: string;
  direction: "ltr" | "rtl";
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageConfig[] = [
  { code: "en", name: "English",    nativeName: "English",    direction: "ltr", flag: "🇬🇧" },
  { code: "hi", name: "Hindi",      nativeName: "हिन्दी",      direction: "ltr", flag: "🇮🇳" },
  { code: "mr", name: "Marathi",    nativeName: "मराठी",       direction: "ltr", flag: "🇮🇳" },
  { code: "es", name: "Spanish",    nativeName: "Español",    direction: "ltr", flag: "🇪🇸" },
  { code: "de", name: "German",     nativeName: "Deutsch",    direction: "ltr", flag: "🇩🇪" },
  { code: "fr", name: "French",     nativeName: "Français",   direction: "ltr", flag: "🇫🇷" },
  { code: "ar", name: "Arabic",     nativeName: "العربية",     direction: "rtl", flag: "🇸🇦" },
  { code: "zh", name: "Chinese",    nativeName: "中文",        direction: "ltr", flag: "🇨🇳" },
  { code: "ja", name: "Japanese",   nativeName: "日本語",      direction: "ltr", flag: "🇯🇵" },
  { code: "pt", name: "Portuguese", nativeName: "Português",  direction: "ltr", flag: "🇧🇷" },
  { code: "ru", name: "Russian",    nativeName: "Русский",    direction: "ltr", flag: "🇷🇺" },
];

// ─── Translation Loader ──────────────────────────────────────────
type TranslationData = Record<string, Record<string, string>>;

const translationCache: Record<string, TranslationData> = {};

async function loadTranslations(locale: string): Promise<TranslationData> {
  if (translationCache[locale]) return translationCache[locale];
  
  try {
    const mod = await import(`./locales/${locale}.json`);
    translationCache[locale] = mod.default || mod;
    return translationCache[locale];
  } catch {
    // Fallback to English
    if (locale !== "en") {
      console.warn(`[i18n] Translation file for '${locale}' not found, falling back to English.`);
      return loadTranslations("en");
    }
    return {};
  }
}

// Preload English
loadTranslations("en");

// ─── Context Types ───────────────────────────────────────────────
interface I18nContextType {
  locale: string;
  direction: "ltr" | "rtl";
  setLocale: (locale: string) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  languages: LanguageConfig[];
  currentLanguage: LanguageConfig;
  isLoading: boolean;
}

const I18nContext = createContext<I18nContextType | null>(null);

// ─── Deep get helper ─────────────────────────────────────────────
function getNestedValue(obj: any, path: string): string | undefined {
  return path.split(".").reduce((acc, part) => acc?.[part], obj);
}

// ─── Provider ────────────────────────────────────────────────────
export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<string>("en");
  const [translations, setTranslations] = useState<TranslationData>({});
  const [fallback, setFallback] = useState<TranslationData>({});
  const [isLoading, setIsLoading] = useState(true);

  const currentLanguage = SUPPORTED_LANGUAGES.find(l => l.code === locale) || SUPPORTED_LANGUAGES[0];
  const direction = currentLanguage.direction;

  // Load translations when locale changes
  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);

    Promise.all([
      loadTranslations(locale),
      loadTranslations("en"),
    ]).then(([localeData, enData]) => {
      if (!cancelled) {
        setTranslations(localeData);
        setFallback(enData);
        setIsLoading(false);
      }
    });

    return () => { cancelled = true; };
  }, [locale]);

  // Apply HTML dir and lang attributes
  useEffect(() => {
    document.documentElement.setAttribute("dir", direction);
    document.documentElement.setAttribute("lang", locale);
    
    // Add/remove RTL class for global CSS
    if (direction === "rtl") {
      document.documentElement.classList.add("rtl");
    } else {
      document.documentElement.classList.remove("rtl");
    }
  }, [direction, locale]);

  // Restore saved locale
  useEffect(() => {
    const saved = localStorage.getItem("axonhis_locale");
    if (saved && SUPPORTED_LANGUAGES.some(l => l.code === saved)) {
      setLocaleState(saved);
    }
  }, []);

  const setLocale = useCallback((newLocale: string) => {
    if (SUPPORTED_LANGUAGES.some(l => l.code === newLocale)) {
      setLocaleState(newLocale);
      localStorage.setItem("axonhis_locale", newLocale);
      
      // Persist to user profile backend (fire and forget)
      try {
        const token = localStorage.getItem("access_token");
        if (token) {
          fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:9500"}/api/v1/auth/preferences`, {
            method: "PUT",
            headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify({ preferred_language: newLocale }),
          }).catch(() => {});
        }
      } catch {}
    }
  }, []);

  // Translation function with fallback and interpolation
  const t = useCallback((key: string, params?: Record<string, string | number>): string => {
    let value = getNestedValue(translations, key) || getNestedValue(fallback, key) || key;
    
    // Interpolate {param} placeholders
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        value = value.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
      });
    }
    
    return value;
  }, [translations, fallback]);

  return (
    <I18nContext.Provider value={{
      locale,
      direction,
      setLocale,
      t,
      languages: SUPPORTED_LANGUAGES,
      currentLanguage,
      isLoading,
    }}>
      {children}
    </I18nContext.Provider>
  );
}

// ─── Hook ────────────────────────────────────────────────────────
export function useTranslation() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    // Return a safe fallback for components outside provider
    return {
      locale: "en",
      direction: "ltr" as const,
      setLocale: () => {},
      t: (key: string) => key,
      languages: SUPPORTED_LANGUAGES,
      currentLanguage: SUPPORTED_LANGUAGES[0],
      isLoading: false,
    };
  }
  return ctx;
}

export default I18nProvider;
