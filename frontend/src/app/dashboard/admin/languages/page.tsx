"use client";
import React, { useState, useRef } from "react";
import { useTranslation, SUPPORTED_LANGUAGES } from "@/i18n";

// Import all locale files for the admin panel
import enJson from "@/i18n/locales/en.json";
import hiJson from "@/i18n/locales/hi.json";
import mrJson from "@/i18n/locales/mr.json";
import esJson from "@/i18n/locales/es.json";
import deJson from "@/i18n/locales/de.json";
import frJson from "@/i18n/locales/fr.json";
import arJson from "@/i18n/locales/ar.json";
import zhJson from "@/i18n/locales/zh.json";
import jaJson from "@/i18n/locales/ja.json";
import ptJson from "@/i18n/locales/pt.json";
import ruJson from "@/i18n/locales/ru.json";

const ALL_LOCALES: Record<string, any> = { en: enJson, hi: hiJson, mr: mrJson, es: esJson, de: deJson, fr: frJson, ar: arJson, zh: zhJson, ja: jaJson, pt: ptJson, ru: ruJson };

function flattenObject(obj: any, prefix = ""): Record<string, string> {
  const result: Record<string, string> = {};
  for (const key of Object.keys(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof obj[key] === "object" && obj[key] !== null) {
      Object.assign(result, flattenObject(obj[key], fullKey));
    } else {
      result[fullKey] = String(obj[key]);
    }
  }
  return result;
}

export default function LanguageManagementPage() {
  const { t } = useTranslation();
  const [selectedLang, setSelectedLang] = useState("en");
  const [searchKey, setSearchKey] = useState("");
  const [showMissingOnly, setShowMissingOnly] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const enFlat = flattenObject(enJson);
  const allKeys = Object.keys(enFlat).sort();
  const selectedFlat = flattenObject(ALL_LOCALES[selectedLang] || {});

  // Coverage stats per language
  const langStats = SUPPORTED_LANGUAGES.map(lang => {
    const flat = flattenObject(ALL_LOCALES[lang.code] || {});
    const translated = allKeys.filter(k => flat[k] && flat[k] !== enFlat[k]).length;
    return { ...lang, total: allKeys.length, translated, coverage: Math.round((translated / allKeys.length) * 100) };
  });

  const selectedLangConfig = SUPPORTED_LANGUAGES.find(l => l.code === selectedLang);

  // Filter keys
  const filteredKeys = allKeys.filter(key => {
    if (searchKey && !key.toLowerCase().includes(searchKey.toLowerCase()) && !enFlat[key].toLowerCase().includes(searchKey.toLowerCase())) return false;
    if (showMissingOnly && selectedFlat[key]) return false;
    return true;
  });

  const handleExport = () => {
    const data = ALL_LOCALES[selectedLang] || {};
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedLang}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-[var(--text-primary)] flex items-center gap-3">
          <div className="bg-gradient-to-br from-violet-500 to-purple-600 p-2.5 rounded-xl text-white shadow-lg">
            🌐
          </div>
          {t("admin.languageManagement")}
        </h1>
        <p className="text-[var(--text-secondary)] mt-2 text-sm">
          Manage translations across all {SUPPORTED_LANGUAGES.length} supported languages. Add, edit, import/export translation files and detect missing keys.
        </p>
      </div>

      {/* Language Coverage Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
        {langStats.map(lang => (
          <button
            key={lang.code}
            onClick={() => setSelectedLang(lang.code)}
            className={`card p-4 text-left transition-all duration-200 hover:shadow-md cursor-pointer ${
              selectedLang === lang.code ? "ring-2 ring-indigo-500 shadow-lg" : ""
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">{lang.flag}</span>
              <div>
                <p className="font-semibold text-sm text-slate-800">{lang.nativeName}</p>
                <p className="text-[10px] text-slate-400">{lang.name} {lang.direction === "rtl" ? "(RTL)" : ""}</p>
              </div>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 mb-1">
              <div
                className={`h-2 rounded-full transition-all ${
                  lang.coverage >= 90 ? "bg-emerald-500" : lang.coverage >= 50 ? "bg-amber-500" : "bg-red-400"
                }`}
                style={{ width: `${lang.code === "en" ? 100 : lang.coverage}%` }}
              />
            </div>
            <p className="text-[11px] text-slate-500">
              {lang.code === "en" ? `${lang.total} keys (base)` : `${lang.translated}/${lang.total} (${lang.coverage}%)`}
            </p>
          </button>
        ))}
      </div>

      {/* Actions Bar */}
      <div className="card mb-6">
        <div className="card-body flex flex-wrap items-center gap-3">
          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search translation keys or values..."
              className="input-field"
              value={searchKey}
              onChange={e => setSearchKey(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={showMissingOnly}
              onChange={e => setShowMissingOnly(e.target.checked)}
              className="w-4 h-4 rounded border-slate-300 text-indigo-600"
            />
            {t("admin.missingTranslations")}
          </label>
          <button onClick={handleExport} className="btn-secondary text-sm">
            📥 {t("admin.exportTranslations")}
          </button>
          <button onClick={() => fileInputRef.current?.click()} className="btn-secondary text-sm">
            📤 {t("admin.importTranslations")}
          </button>
          <input ref={fileInputRef} type="file" accept=".json" className="hidden" />
        </div>
      </div>

      {/* Translation Table */}
      <div className="card overflow-hidden">
        <div className="card-header">
          <h3 className="font-semibold flex items-center gap-2">
            {selectedLangConfig?.flag} {selectedLangConfig?.nativeName}
            <span className="text-slate-400 font-normal text-sm">— {filteredKeys.length} keys</span>
          </h3>
        </div>
        <div className="max-h-[60vh] overflow-y-auto">
          <table className="data-table">
            <thead className="sticky top-0 z-10">
              <tr>
                <th className="w-[280px]">{t("admin.translationKeys")}</th>
                <th>English (Base)</th>
                <th>
                  {selectedLangConfig?.nativeName || selectedLang}
                  {selectedLang !== "en" && (
                    <span className="ml-2 text-[10px] font-normal text-slate-400">
                      ({langStats.find(l => l.code === selectedLang)?.coverage}% {t("admin.coverage")})
                    </span>
                  )}
                </th>
                <th className="w-20">{t("common.status")}</th>
              </tr>
            </thead>
            <tbody>
              {filteredKeys.map(key => {
                const hasTranslation = selectedFlat[key] && (selectedLang === "en" || selectedFlat[key] !== enFlat[key]);
                return (
                  <tr key={key}>
                    <td className="font-mono text-xs text-indigo-600 break-all">{key}</td>
                    <td className="text-sm text-slate-700">{enFlat[key]}</td>
                    <td className="text-sm">
                      {selectedLang === "en" ? (
                        <span className="text-slate-700">{enFlat[key]}</span>
                      ) : selectedFlat[key] ? (
                        <span className="text-slate-700">{selectedFlat[key]}</span>
                      ) : (
                        <span className="text-slate-300 italic">— missing —</span>
                      )}
                    </td>
                    <td>
                      {hasTranslation ? (
                        <span className="badge-success text-[10px]">✓</span>
                      ) : selectedLang === "en" ? (
                        <span className="badge-info text-[10px]">Base</span>
                      ) : (
                        <span className="badge-warning text-[10px]">Missing</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
