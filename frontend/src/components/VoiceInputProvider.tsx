"use client";
import React, { useEffect, useRef, useCallback } from "react";

/* ═══════════════════════════════════════════════════════════════════════════
   GLOBAL VOICE INPUT PROVIDER
   Auto-injects a microphone button on every <input> and <textarea> field.
   Uses Web Speech API (SpeechRecognition) for speech-to-text.
   ═══════════════════════════════════════════════════════════════════════════ */

const VOICE_ATTR = "data-voice-enabled";
const MIC_BTN_CLASS = "axon-voice-mic-btn";

// SVG icons as strings for injection
const MIC_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>`;
const MIC_OFF_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="2" x2="22" y1="2" y2="22"/><path d="M18.89 13.23A7.12 7.12 0 0 0 19 12v-2"/><path d="M5 10v2a7 7 0 0 0 12 5"/><path d="M15 9.34V5a3 3 0 0 0-5.68-1.33"/><path d="M9 9v3a3 3 0 0 0 5.12 2.12"/><line x1="12" x2="12" y1="19" y2="22"/></svg>`;
const STOP_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>`;

function getSpeechRecognition(): any {
  if (typeof window === "undefined") return null;
  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;
}

function detectLanguage(): string {
  if (typeof document === "undefined") return "en-US";
  const htmlLang = document.documentElement.lang || "en";
  const langMap: Record<string, string> = {
    en: "en-US",
    ar: "ar-SA",
    hi: "hi-IN",
    mr: "mr-IN",
    ur: "ur-PK",
    fr: "fr-FR",
    es: "es-ES",
    de: "de-DE",
  };
  return langMap[htmlLang.split("-")[0]] || "en-US";
}

function triggerReactChange(el: HTMLInputElement | HTMLTextAreaElement, value: string) {
  // For React controlled inputs, we need to use the native setter
  const nativeInputValueSetter =
    Object.getOwnPropertyDescriptor(
      el.tagName === "TEXTAREA"
        ? window.HTMLTextAreaElement.prototype
        : window.HTMLInputElement.prototype,
      "value"
    )?.set;

  if (nativeInputValueSetter) {
    nativeInputValueSetter.call(el, value);
  } else {
    el.value = value;
  }

  // Dispatch both input and change events for React compatibility
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
}

function createMicButton(input: HTMLInputElement | HTMLTextAreaElement) {
  // Skip if already has a mic, or if input type is not text-compatible
  if (input.getAttribute(VOICE_ATTR)) return;
  const skipTypes = ["file", "hidden", "checkbox", "radio", "submit", "button", "reset", "image", "range", "color"];
  if (input.tagName === "INPUT" && skipTypes.includes((input as HTMLInputElement).type)) return;
  // Skip date/time inputs
  const dateTypes = ["date", "time", "datetime-local", "month", "week"];
  if (input.tagName === "INPUT" && dateTypes.includes((input as HTMLInputElement).type)) return;

  const SpeechRecognition = getSpeechRecognition();
  if (!SpeechRecognition) return;

  input.setAttribute(VOICE_ATTR, "true");

  // Wrap the input if not already wrapped
  const parent = input.parentElement;
  if (!parent) return;

  // Create wrapper if the parent isn't already a voice wrapper
  let wrapper: HTMLElement;
  if (parent.classList.contains("axon-voice-wrapper")) {
    wrapper = parent;
  } else {
    wrapper = document.createElement("div");
    wrapper.className = "axon-voice-wrapper";
    // Preserve the input's position in DOM
    parent.insertBefore(wrapper, input);
    wrapper.appendChild(input);
  }

  // Create button
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = MIC_BTN_CLASS;
  btn.innerHTML = MIC_SVG;
  btn.title = "Voice input – Click to speak";
  btn.setAttribute("aria-label", "Voice input");
  btn.tabIndex = -1;

  let recognition: any = null;
  let isListening = false;

  const startListening = () => {
    recognition = new SpeechRecognition();
    recognition.lang = detectLanguage();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;

    btn.classList.add("axon-voice-active");
    btn.innerHTML = STOP_SVG;
    btn.title = "Listening… Click to stop";
    isListening = true;

    // Show visual feedback
    const indicator = document.createElement("span");
    indicator.className = "axon-voice-indicator";
    indicator.textContent = "🎤 Listening...";
    wrapper.appendChild(indicator);

    recognition.onresult = (event: any) => {
      let finalTranscript = "";
      let interimTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript = transcript;
        }
      }

      if (finalTranscript) {
        // Append or replace based on existing content
        const currentValue = input.value;
        const newValue = currentValue
          ? currentValue + (currentValue.endsWith(" ") ? "" : " ") + finalTranscript
          : finalTranscript;
        triggerReactChange(input, newValue);
        indicator.textContent = "✅ " + finalTranscript.slice(0, 30) + (finalTranscript.length > 30 ? "…" : "");
        indicator.classList.add("axon-voice-success");
      } else if (interimTranscript) {
        indicator.textContent = "🎤 " + interimTranscript.slice(0, 40) + "…";
      }
    };

    recognition.onerror = (event: any) => {
      console.warn("Voice input error:", event.error);
      indicator.textContent = event.error === "no-speech"
        ? "No speech detected. Try again."
        : "⚠️ Error: " + event.error;
      indicator.classList.add("axon-voice-error");
      stopListening();
    };

    recognition.onend = () => {
      stopListening();
    };

    try {
      recognition.start();
    } catch (err) {
      console.warn("Failed to start speech recognition:", err);
      stopListening();
    }
  };

  const stopListening = () => {
    isListening = false;
    btn.classList.remove("axon-voice-active");
    btn.innerHTML = MIC_SVG;
    btn.title = "Voice input – Click to speak";

    if (recognition) {
      try { recognition.stop(); } catch {}
      recognition = null;
    }

    // Remove indicator after delay
    const indicator = wrapper.querySelector(".axon-voice-indicator");
    if (indicator) {
      setTimeout(() => {
        indicator.classList.add("axon-voice-fade-out");
        setTimeout(() => indicator.remove(), 300);
      }, 1500);
    }

    // Focus the input after voice input
    input.focus();
  };

  btn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  });

  wrapper.appendChild(btn);
}

function processAllInputs() {
  const inputs = document.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(
    `input:not([${VOICE_ATTR}]), textarea:not([${VOICE_ATTR}])`
  );
  inputs.forEach(createMicButton);
}

export default function VoiceInputProvider({ children }: { children: React.ReactNode }) {
  const observerRef = useRef<MutationObserver | null>(null);

  const handleMutations = useCallback((mutations: MutationRecord[]) => {
    let hasNewNodes = false;
    for (const mutation of mutations) {
      if (mutation.addedNodes.length > 0) {
        hasNewNodes = true;
        break;
      }
    }
    if (hasNewNodes) {
      // Debounce to avoid excessive processing
      requestAnimationFrame(processAllInputs);
    }
  }, []);

  useEffect(() => {
    // Check if Speech Recognition is supported
    if (!getSpeechRecognition()) {
      console.warn("AxonHIS Voice Input: Web Speech API not supported in this browser.");
      return;
    }

    // Process existing inputs
    const timer = setTimeout(processAllInputs, 500);

    // Watch for new inputs being added dynamically
    observerRef.current = new MutationObserver(handleMutations);
    observerRef.current.observe(document.body, {
      childList: true,
      subtree: true,
    });

    // Re-process on route changes (Next.js SPA navigation)
    const handleRouteChange = () => {
      setTimeout(processAllInputs, 300);
    };

    // Listen for popstate (back/forward navigation)
    window.addEventListener("popstate", handleRouteChange);

    // Periodic check for new unprocessed inputs (handles lazy-loaded components)
    const interval = setInterval(processAllInputs, 2000);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
      window.removeEventListener("popstate", handleRouteChange);
      observerRef.current?.disconnect();
    };
  }, [handleMutations]);

  return <>{children}</>;
}
