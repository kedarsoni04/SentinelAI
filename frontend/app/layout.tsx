import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SentinelAI — Intelligent Surveillance & Threat Detection',
  description:
    'AI-powered security operations platform for intelligent surveillance, threat detection, and incident management.',
  keywords: ['security', 'surveillance', 'AI', 'threat detection', 'SOC'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0a0d12] text-[#e8edf5] antialiased">
        {children}
      </body>
    </html>
  );
}
