import { Plane, Github, ExternalLink } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border bg-muted/50 py-8">
      <div className="container mx-auto px-4">
        <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-between">
          {/* Brand */}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Plane className="h-4 w-4 text-blue-500" />
            <span className="text-sm font-medium">TripMate AI</span>
            <span className="text-xs">— LangGraph Multi-Agent Travel Planner</span>
          </div>

          {/* Tech stack */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
              LangGraph
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-orange-500" />
              Groq / Llama 3
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-blue-500" />
              FastAPI
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full bg-purple-500" />
              Next.js 14
            </span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              <Github className="h-3 w-3" />
              Source
            </a>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              <ExternalLink className="h-3 w-3" />
              API Docs
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
