import type { Metadata } from "next";
import "./globals.css";
import { I18nProvider } from "@/i18n";
import VoiceInputProvider from "@/components/VoiceInputProvider";

export const metadata: Metadata = {
  title: "AXONHIS – Hospital Information System",
  description: "AI-First Hospital Information System for OPD, IPD, ER, Lab, Pharmacy, and Billing.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <I18nProvider>
          <VoiceInputProvider>{children}</VoiceInputProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
