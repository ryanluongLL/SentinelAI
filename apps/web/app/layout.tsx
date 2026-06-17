import type { Metadata } from "next";
import Layout from "@/components/layout/Layout";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentinelAI",
  description: "AI-powered cybersecurity threat detection",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Layout>{children}</Layout>
      </body>
    </html>
  );
}