import Link from "next/link";
import { PushManager } from "@/components/push-manager";

export function Nav() {
  return (
    <header className="sticky top-0 z-10 border-b border-white/10 bg-[#060607]/90 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-3">
        <Link href="/" className="text-sm font-semibold tracking-tight text-white">
          System Design <span className="text-emerald-400">Loop</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm text-white/60">
          <Link href="/" className="hover:text-white">
            Today
          </Link>
          <Link href="/progress" className="hover:text-white">
            Progress
          </Link>
          <PushManager />
        </nav>
      </div>
    </header>
  );
}
