import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Digital Denis | Cognitive OS",
  description: "Personal Cognitive Operating System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <body
        className={`${inter.className} bg-[#050505] text-white antialiased`}
        suppressHydrationWarning
      >
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex-1 overflow-y-auto bg-gradient-to-br from-[#050505] via-[#0a0a0a] to-[#111] p-6 lg:p-10">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
