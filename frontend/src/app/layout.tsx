import type { Metadata } from "next";
import "./globals.css";

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
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
