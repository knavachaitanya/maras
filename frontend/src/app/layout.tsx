import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MARAS - MultiAgent Research & Aggregation",
  description: "AI-powered research aggregation with 5 specialized agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
