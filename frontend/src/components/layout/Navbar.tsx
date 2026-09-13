"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Plane, History, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/10 bg-blue-950/95 backdrop-blur supports-[backdrop-filter]:bg-blue-950/80">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 text-white hover:opacity-90 transition-opacity"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500">
            <Plane className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight">TripMate AI</span>
          <span className="hidden rounded bg-blue-500/20 px-1.5 py-0.5 text-xs font-medium text-blue-300 sm:inline">
            Beta
          </span>
        </Link>

        {/* Navigation links */}
        <div className="flex items-center gap-1">
          <Link
            href="/"
            className={cn(
              "flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              pathname === "/"
                ? "bg-white/10 text-white"
                : "text-blue-200 hover:bg-white/5 hover:text-white"
            )}
          >
            <MapPin className="h-4 w-4" />
            <span className="hidden sm:inline">Plan Trip</span>
          </Link>
          <Link
            href="/history"
            className={cn(
              "flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              pathname === "/history"
                ? "bg-white/10 text-white"
                : "text-blue-200 hover:bg-white/5 hover:text-white"
            )}
          >
            <History className="h-4 w-4" />
            <span className="hidden sm:inline">History</span>
          </Link>
        </div>
      </div>
    </nav>
  );
}
