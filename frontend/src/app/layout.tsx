import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Shell } from "@/components/layout";
import { Providers } from "@/lib/providers";
import { InstallPrompt } from "@/components/pwa";
import { OfflineIndicator } from "@/components/pwa/OfflineIndicator";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Digital Denis | Cognitive OS",
  description: "Твой когнитивный ассистент — Personal Cognitive Operating System",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Digital Denis",
  },
  formatDetection: {
    telephone: false,
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: "#3b82f6",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <body
        className={`${inter.className} bg-zinc-950 text-white antialiased`}
        suppressHydrationWarning
      >
        <Providers>
          <Shell>
            {children}
          </Shell>
          {/* <InstallPrompt /> */}
          {/* <OfflineIndicator /> */}
        </Providers>
      </body>
    </html>
  );
}
