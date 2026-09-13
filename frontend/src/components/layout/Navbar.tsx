"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Plane, History, MapPin, User } from "lucide-react";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <nav
      className={cn(
        "absolute top-0 left-0 right-0 z-50 w-full",
        isHome
          ? "border-b border-white/10 bg-transparent"
          : "sticky border-b border-white/10 bg-blue-950/95 backdrop-blur supports-[backdrop-filter]:bg-blue-950/80"
      )}
    >
      <div className="container mx-auto flex h-16 items-center justify-between px-6">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 text-white hover:opacity-90 transition-opacity"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500 shadow-lg shadow-blue-500/30">
            <Plane className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-bold tracking-tight">TripMate AI</span>
          <span className="rounded-full border border-white/20 bg-white/10 px-2 py-0.5 text-xs font-medium text-white/80">
            Beta
          </span>
        </Link>

        {/* Navigation */}
        <div className="flex items-center gap-2">
          <Link
            href="/"
            className={cn(
              "flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-all",
              pathname === "/"
                ? "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
                : "text-white/80 hover:bg-white/10 hover:text-white"
            )}
          >
            <MapPin className="h-3.5 w-3.5" />
            Plan Trip
          </Link>
          <Link
            href="/history"
            className={cn(
              "flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-all",
              pathname === "/history"
                ? "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
                : "text-white/80 hover:bg-white/10 hover:text-white"
            )}
          >
            <History className="h-3.5 w-3.5" />
            History
          </Link>
          <button className="ml-1 flex h-8 w-8 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white/80 transition-all hover:bg-white/20 hover:text-white">
            <User className="h-4 w-4" />
          </button>
        </div>
      </div>
    </nav>
  );
}
