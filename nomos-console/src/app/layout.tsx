import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NomOS Console",
  description: "AI Agent Fleet Management — EU AI Act Compliant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <nav className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <a href="/" className="text-xl font-bold tracking-tight">
              NomOS <span className="text-sm font-normal text-gray-500">Console</span>
            </a>
            <div className="flex gap-6 text-sm">
              <a href="/fleet" className="text-gray-600 hover:text-gray-900">Fleet</a>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
