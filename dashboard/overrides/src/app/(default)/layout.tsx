import type { Metadata } from "next";
import "../globals.css";
import { DEFAULT_LANG } from "@/lib/i18n";
import { SITE_URL } from "@/lib/metadata";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  icons: { icon: "/favicon.svg" },
};

// An explicit route preserves ISR for default-language vote URLs. In Next
// 15.5, middleware-rewritten on-demand paths can otherwise render uncached.
export default function DefaultLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang={DEFAULT_LANG} className="overflow-x-hidden">
      <body className="bg-surface-1 text-foreground font-sans antialiased flex flex-col min-h-screen">
        {children}
      </body>
    </html>
  );
}
