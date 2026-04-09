import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import VoiceInputProvider from "@/components/VoiceInputProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AxonHIS MD – Unified Clinical Practice Platform",
  description: "Unified Clinical Practice & Health ATM Platform by AxonHIS",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <VoiceInputProvider>{children}</VoiceInputProvider>
      </body>
    </html>
  );
}
