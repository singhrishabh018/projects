import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";
import { ServiceWorkerRegister } from "@/components/service-worker-register";

export const metadata: Metadata = {
  title: "System Design Loop",
  description:
    "A daily, visual, sourced-not-authored system design habit loop -- built on system-design-primer (CC BY 4.0).",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = {
  themeColor: "#060607",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#060607] text-[#f2f2f2]">
        <ServiceWorkerRegister />
        <Nav />
        <main className="mx-auto w-full max-w-5xl flex-1 px-5 py-8">{children}</main>
        <footer className="border-t border-white/10 px-5 py-6 text-center text-xs text-white/30">
          Concept content sourced from{" "}
          <a
            className="underline hover:text-white/60"
            href="https://github.com/donnemartin/system-design-primer"
            target="_blank"
            rel="noreferrer"
          >
            system-design-primer
          </a>{" "}
          (CC BY 4.0). Real-world examples link to their original sources. Nothing here is
          AI-generated prose.
        </footer>
      </body>
    </html>
  );
}
