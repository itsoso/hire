import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KHire - GitHub-Based Talent Recruitment",
  description: "Find top developers by their actual contributions",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <nav className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <a href="/" className="text-2xl font-bold text-indigo-600">
              KHire
            </a>
            <div className="flex gap-6 text-sm font-medium text-gray-600">
              <a href="/" className="hover:text-indigo-600">
                Search
              </a>
              <a href="/analyze" className="hover:text-indigo-600">
                Analyze
              </a>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
